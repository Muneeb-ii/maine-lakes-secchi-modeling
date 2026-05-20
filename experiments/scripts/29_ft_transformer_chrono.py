import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.experimental import enable_iterative_imputer  # noqa: F401 (enables IterativeImputer)
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from tqdm.auto import tqdm

from tab_transformer_pytorch import FTTransformer

from experiment_utils import CanonicalReport, ensure_reports_dir, write_canonical_report, load_data

MAX_TRAIN_ROWS = 30000
MAX_TEST_ROWS = 10000

def evaluate_model(y_true, y_pred, depth):
    if len(y_true) == 0:
        return {"MAE": 0, "RMSE": 0, "R2": 0, "MAE_Norm": 0, "RMSE_Norm": 0}
        
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred) if len(y_true) > 1 else np.nan
    
    safe_depth = np.where(pd.Series(depth).to_numpy() > 0, pd.Series(depth).to_numpy(), np.nan)
    pct_error = (pd.Series(y_true).to_numpy() - pd.Series(y_pred).to_numpy()) / safe_depth
    mae_norm = np.nanmean(np.abs(pct_error))
    mse_norm = np.nanmean(pct_error ** 2)
    rmse_norm = np.sqrt(mse_norm)
    
    return {
        "MAE": mae, "RMSE": rmse, "R2": r2,
        "MAE_Norm": mae_norm, "RMSE_Norm": rmse_norm
    }

def main():
    reports_dir = ensure_reports_dir()
    np.random.seed(42)
    torch.manual_seed(42)
    torch.set_num_threads(max(1, min(8, torch.get_num_threads())))
    print("Loading dataset...")
    data = load_data()
    df = data.frame
    
    target = "SECCHI"
    num_cols = ["LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
    df["year"] = df["SAMPDATE"].dt.year
    df["month"] = df["SAMPDATE"].dt.month
    base_features = ["year", "month"] + num_cols
    
    chem_features = ["DOMAX", "DOMIN", "TPEC", "TPBG", "PH", "COLOR", "CONDUCT", "ALK"]
    valid_chems = [c for c in chem_features if c in df.columns]
    
    subset_cols = [target, "SAMPDATE", "MIDAS"] + num_cols 
    model_df = df.dropna(subset=subset_cols).copy()
    model_df = model_df.sort_values(by="SAMPDATE").reset_index(drop=True)
    
    features = base_features + valid_chems
    
    # 80/20 Chronological Split
    split_idx = int(len(model_df) * 0.8)
    train_df = model_df.iloc[:split_idx]
    test_df = model_df.iloc[split_idx:]
    if train_df.empty or test_df.empty:
        raise ValueError("Chronological 80/20 split produced an empty train or test set.")
    
    X_train = train_df[features].copy()
    y_train = train_df[target].copy()
    X_test = test_df[features].copy()
    y_test = test_df[target].copy()
    depth_test = test_df["DEPTH_MAX_FEET"]

    if len(X_train) > MAX_TRAIN_ROWS:
        X_train = X_train.iloc[-MAX_TRAIN_ROWS:].copy()
        y_train = y_train.iloc[-MAX_TRAIN_ROWS:].copy()
    if len(X_test) > MAX_TEST_ROWS:
        X_test = X_test.iloc[:MAX_TEST_ROWS].copy()
        y_test = y_test.iloc[:MAX_TEST_ROWS].copy()
        depth_test = depth_test.iloc[:MAX_TEST_ROWS].copy()
    
    print("\nFitting MissForest (IterativeImputer with RandomForest)...")
    rf_imputer = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=1)
    imputer = IterativeImputer(estimator=rf_imputer, max_iter=3, random_state=42)
    
    X_train_imp = imputer.fit_transform(X_train)
    X_test_imp = imputer.transform(X_test)
    
    print("Scaling Data for Deep Learning...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_imp)
    X_test_scaled = scaler.transform(X_test_imp)
    
    # Convert to PyTorch tensors
    X_train_t = torch.tensor(X_train_scaled, dtype=torch.float32)
    y_train_t = torch.tensor(y_train.values, dtype=torch.float32)
    X_test_t = torch.tensor(X_test_scaled, dtype=torch.float32)
    
    train_dataset = TensorDataset(X_train_t, y_train_t)
    train_loader = DataLoader(train_dataset, batch_size=2048, shuffle=True)
    
    print("Training FT-Transformer Model...")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # FTTransformer Initialization
    # We treat all features as continuous to maintain parity with RF and MLP tests.
    model = FTTransformer(
        categories = (),                # No categoricals
        num_continuous = len(features), # All features are continuous
        dim = 16,                       # Transformer token dimension
        dim_out = 1,                    # Regressing to 1 value (Secchi)
        depth = 2,                      # 2 Transformer blocks
        heads = 4,                      # 4 attention heads
        attn_dropout = 0.1,
        ff_dropout = 0.1
    ).to(device)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    epochs = 8
    train_losses = []
    
    model.train()
    epoch_bar = tqdm(range(epochs), desc="FT-Transformer epochs", unit="epoch")
    for epoch in epoch_bar:
        epoch_loss = 0.0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            # Empty tensor for categoricals since we have none
            batch_C = torch.empty((batch_X.shape[0], 0), dtype=torch.long).to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_C, batch_X).squeeze(1)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item() * batch_X.size(0)
            
        epoch_loss /= len(train_loader.dataset)
        train_losses.append(epoch_loss)
        epoch_bar.set_postfix(loss=f"{epoch_loss:.4f}")
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs} | Loss: {epoch_loss:.4f}")
    epoch_bar.close()
            
    # Plot Training Loss
    plt.figure(figsize=(8, 5))
    plt.plot(range(1, epochs + 1), train_losses, color='green', marker='o')
    plt.title("FT-Transformer Training Loss over Epochs")
    plt.xlabel("Epoch")
    plt.ylabel("MSE Loss")
    plt.grid(True, alpha=0.3)
    loss_plot_path = reports_dir / "29_ft_transformer_training_loss.png"
    plt.savefig(loss_plot_path, bbox_inches="tight")
    plt.close()
    
    print("Evaluating Model...")
    model.eval()
    with torch.no_grad():
        x_cont_test = X_test_t.to(device)
        x_categ_test = torch.empty((x_cont_test.shape[0], 0), dtype=torch.long).to(device)
        preds_t = model(x_categ_test, x_cont_test).squeeze(1)
        y_pred = preds_t.cpu().numpy()
        
    metrics = evaluate_model(y_test, y_pred, depth_test)
    
    report = CanonicalReport(
        objective=(
            "Benchmark an FT-Transformer on the same MissForest-imputed chronological split "
            "used by the other advanced tabular baselines."
        ),
        method=(
            "Apply the Experiment 22 feature policy and chronological 80/20 split, impute the "
            "feature matrix with IterativeImputer plus RandomForest, standardize the imputed "
            "inputs, cap the train/test row counts for tractable CPU execution, and train an "
            "FT-Transformer regressor on the sampled training slice only."
        ),
        parameters=(
            "Imputation and preprocessing:\n"
            "- `IterativeImputer`\n"
            "- estimator: `RandomForestRegressor`\n"
            "- `n_estimators=50`\n"
            "- `max_depth=10`\n"
            "- `max_iter=3`\n"
            "- `StandardScaler`\n"
            f"- training rows capped at `{MAX_TRAIN_ROWS}`\n"
            f"- test rows capped at `{MAX_TEST_ROWS}`\n\n"
            "FT-Transformer:\n"
            "- `dim=16`\n"
            "- `depth=2`\n"
            "- `heads=4`\n"
            "- `attn_dropout=0.1`\n"
            "- `ff_dropout=0.1`\n"
            "- optimizer: `Adam(lr=0.001)`\n"
            "- `epochs=8`\n"
            "- `batch_size=2048`\n\n"
            "Feature policy: baseline geographic and temporal features plus valid chemistry columns, "
            "excluding `CHLA`."
        ),
        results=(
            "### Chronological Test Metrics\n\n"
            f"- R^2: {metrics['R2']:.4f}\n"
            f"- MSE: {(metrics['RMSE']**2):.4f} m^2\n"
            f"- MAE: {metrics['MAE']:.4f} m\n"
            f"- Normalized MSE: {(metrics['RMSE_Norm']**2):.4f}\n"
            f"- Normalized MAE: {metrics['MAE_Norm']:.4f}\n\n"
            "### Training Diagnostics\n\n"
            "The figure below records epoch-level training loss for the final run.\n\n"
            "![FT-Transformer Training Loss](29_ft_transformer_training_loss.png)"
        ),
        next_step=(
            "Compare this deep-learning baseline directly against the MissForest RandomForest, "
            "MLP, and TabNet results before deciding whether transformer-based tabular models "
            "deserve a place in the final dashboard model shortlist."
        ),
    )

    report_path = write_canonical_report(
        "29_ft_transformer_chrono.md",
        "Experiment 29: FT-Transformer Chronological Baseline",
        report,
    )
    print(f"\nReport generated at {report_path}")

if __name__ == "__main__":
    main()
