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

from experiment_utils import ensure_reports_dir, write_markdown_report, load_data

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

class TabularMLP(nn.Module):
    def __init__(self, input_dim):
        super(TabularMLP, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        
    def forward(self, x):
        return self.net(x).squeeze(1)

def main():
    reports_dir = ensure_reports_dir()
    np.random.seed(42)
    torch.manual_seed(42)
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
    
    print("\nFitting MissForest (IterativeImputer with RandomForest)...")
    rf_imputer = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
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
    
    # Create DataLoaders
    train_dataset = TensorDataset(X_train_t, y_train_t)
    train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
    
    # Initialize Model, Loss, Optimizer
    print("Training Tabular MLP Model...")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = TabularMLP(input_dim=len(features)).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    epochs = 40
    train_losses = []
    
    model.train()
    epoch_bar = tqdm(range(epochs), desc="MLP epochs", unit="epoch")
    for epoch in epoch_bar:
        epoch_loss = 0.0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_X)
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
    plt.plot(range(1, epochs + 1), train_losses, color='blue', marker='o')
    plt.title("MLP Training Loss over Epochs")
    plt.xlabel("Epoch")
    plt.ylabel("MSE Loss")
    plt.grid(True, alpha=0.3)
    loss_plot_path = reports_dir / "27_mlp_training_loss.png"
    plt.savefig(loss_plot_path, bbox_inches="tight")
    plt.close()
    
    # Evaluate
    print("Evaluating Model...")
    model.eval()
    with torch.no_grad():
        preds_t = model(X_test_t.to(device))
        y_pred = preds_t.cpu().numpy()
        
    metrics = evaluate_model(y_test, y_pred, depth_test)
    
    sections = [
        ("What We Did",
         "In this experiment, we replaced the Random Forest predictor with a **Multi-Layer Perceptron (MLP)**. This serves as our Deep Learning baseline for tabular data.\n\n"
         "We followed this process:\n"
         "1. Extracted all lakes using the baseline geographical and chemical features.\n"
         "2. Chronologically split the data into 80% global train / 20% global test.\n"
         "3. Applied `MissForest` imputation to infer missing chemistry (strictly trained on the 80% split).\n"
         "4. **[NEW]** Applied `StandardScaler` to ensure all features had a mean of 0 and variance of 1, which is critical for neural network convergence.\n"
         "5. Trained a 4-layer PyTorch MLP (`256 -> 128 -> 64 -> 1`) with ReLU activations and Dropout (0.2) for 40 epochs using Adam."
        ),
        
        ("80/20 Chronological Results (MLP)",
         "The performance of the Feed-Forward Neural Network on the global chronological test set:\n\n"
         f"- **R-Squared (R²):** {metrics['R2']:.4f}\n"
         f"- **Mean Squared Error (MSE):** {(metrics['RMSE']**2):.4f} meters²\n"
         f"- **Mean Absolute Error (MAE):** {metrics['MAE']:.4f} meters\n"
         f"- **Normalized MSE:** {(metrics['RMSE_Norm']**2):.4f}\n"
         f"- **Normalized MAE:** {metrics['MAE_Norm']:.4f}\n\n"
         "Note: normalized errors divide SECCHI residuals by `DEPTH_MAX_FEET`, so this is a depth-relative ratio.\n\n"
         "![MLP Training Loss](27_mlp_training_loss.png)"
        ),
        
        ("Interpretations",
         "### MLP vs. Random Forest\n\n"
         "By comparing this MLP directly to **Experiment 22**, we can observe the difference between tree-based partitioning and deep dense networks on this specific water quality dataset.\n"
         "Standard feed-forward neural networks typically struggle on tabular data compared to Random Forests because tabular features lack the spatial or temporal continuity that neural networks exploit in images or text. If this model underperforms Experiment 22, it validates the need for specialized Tabular Deep Learning architectures like TabNet or FT-Transformer."
        )
    ]
    
    report_path = write_markdown_report("27_mlp_chrono.md", "Experiment 27: Multi-Layer Perceptron (Deep Learning Baseline)", sections)
    print(f"\nReport generated at {report_path}")

if __name__ == "__main__":
    main()
