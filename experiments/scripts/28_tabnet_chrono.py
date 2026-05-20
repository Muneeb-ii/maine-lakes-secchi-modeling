import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.experimental import enable_iterative_imputer  # noqa: F401 (enables IterativeImputer)
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

from pytorch_tabnet.tab_model import TabNetRegressor
from pytorch_tabnet.callbacks import Callback
import torch
from tqdm.auto import tqdm

from experiment_utils import ensure_reports_dir, write_markdown_report, df_to_markdown_table, load_data


class TqdmEpochCallback(Callback):
    def __init__(self, total_epochs):
        super().__init__()
        self.total_epochs = total_epochs
        self._bar = None

    def on_train_begin(self, logs=None):
        self._bar = tqdm(total=self.total_epochs, desc="TabNet epochs", unit="epoch")

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        if self._bar is None:
            return
        self._bar.update(1)
        loss = logs.get("loss")
        val = logs.get("val_0_mse") or logs.get("val_mse") or logs.get("valid_mse")
        if loss is not None:
            postfix = {"loss": f"{loss:.4f}"}
            if val is not None:
                postfix["val_mse"] = f"{val:.4f}"
            self._bar.set_postfix(postfix)

    def on_train_end(self, logs=None):
        if self._bar is not None:
            self._bar.close()
            self._bar = None

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

    # Keep the final test set strictly untouched during training/early stopping.
    val_split_idx = int(len(X_train_imp) * 0.9)
    X_fit_imp = X_train_imp[:val_split_idx]
    y_fit = y_train.values[:val_split_idx]
    X_val_imp = X_train_imp[val_split_idx:]
    y_val = y_train.values[val_split_idx:]
    if len(X_fit_imp) == 0 or len(X_val_imp) == 0:
        raise ValueError("Training-window 90/10 validation split produced an empty fit or validation set.")
    
    print("Scaling Data for TabNet...")
    scaler = StandardScaler()
    X_fit_scaled = np.float32(scaler.fit_transform(X_fit_imp))
    X_val_scaled = np.float32(scaler.transform(X_val_imp))
    X_test_scaled = np.float32(scaler.transform(X_test_imp))
    
    # TabNet requires NumPy arrays
    y_fit_arr = np.float32(y_fit.reshape(-1, 1))
    y_val_arr = np.float32(y_val.reshape(-1, 1))
    y_test_arr = np.float32(y_test.values.reshape(-1, 1))
    
    print("Training TabNetRegressor...")
    device_name = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    
    # Initialize TabNet
    clf = TabNetRegressor(
        n_d=64, n_a=64, n_steps=5,
        gamma=1.5, n_independent=2, n_shared=2,
        optimizer_fn=torch.optim.Adam,
        optimizer_params=dict(lr=2e-2),
        scheduler_params={"step_size":50, "gamma":0.9},
        scheduler_fn=torch.optim.lr_scheduler.StepLR,
        mask_type='entmax',
        device_name=device_name,
        seed=42
    )
    
    clf.fit(
        X_train=X_fit_scaled, y_train=y_fit_arr,
        eval_set=[(X_fit_scaled, y_fit_arr), (X_val_scaled, y_val_arr)],
        eval_name=['train', 'val'],
        eval_metric=['mse'],
        max_epochs=100, patience=20,
        batch_size=1024, virtual_batch_size=128,
        num_workers=0,
        drop_last=False,
        pin_memory=False,
        callbacks=[TqdmEpochCallback(total_epochs=100)]
    )
    
    print("Evaluating Model...")
    y_pred = clf.predict(X_test_scaled)
    metrics = evaluate_model(y_test, y_pred.flatten(), depth_test)
    
    # Plot Training Loss
    plt.figure(figsize=(8, 5))
    plt.plot(clf.history['train_mse'], label='Train MSE', color='blue')
    plt.plot(clf.history['val_mse'], label='Validation MSE', color='orange')
    plt.title("TabNet Training History")
    plt.xlabel("Epoch")
    plt.ylabel("MSE Loss")
    plt.legend()
    plt.grid(True, alpha=0.3)
    loss_plot_path = reports_dir / "28_tabnet_training_loss.png"
    plt.savefig(loss_plot_path, bbox_inches="tight")
    plt.close()
    
    # Feature Importances Plot
    importances = clf.feature_importances_
    imp_df = pd.DataFrame({"Feature": features, "Importance": importances})
    imp_df = imp_df.sort_values(by="Importance", ascending=False).reset_index(drop=True)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x="Importance", y="Feature", data=imp_df, color='purple')
    plt.title("TabNet Feature Importances (Sequential Attention)")
    plt.xlabel("Global Feature Importance Weight")
    plot_path = reports_dir / "28_tabnet_importances.png"
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()
    
    sections = [
        ("What We Did",
         "In this experiment, we utilized **TabNet (by Google)**, a state-of-the-art Deep Learning architecture specifically designed for tabular data. "
         "Unlike standard neural networks, TabNet uses 'sequential attention' to choose which features to look at during each step of prediction, effectively mimicking the behavior of a Random Forest but using deep learning.\n\n"
         "We followed this process:\n"
         "1. Applied the same 80/20 chronological split and `MissForest` imputation as Experiment 22.\n"
         "2. Built an internal 90/10 split inside the training window to create a chronological validation set.\n"
         "3. Scaled the imputed features using `StandardScaler`.\n"
         "4. Trained the `TabNetRegressor` using an Adam optimizer, tracking MSE on the validation split for early stopping (the final test set remained untouched until final scoring)."
        ),
        
        ("80/20 Chronological Results (TabNet)",
         "The performance of TabNet on the global chronological test set:\n\n"
         f"- **R-Squared (R²):** {metrics['R2']:.4f}\n"
         f"- **Mean Squared Error (MSE):** {(metrics['RMSE']**2):.4f} meters²\n"
         f"- **Mean Absolute Error (MAE):** {metrics['MAE']:.4f} meters\n"
         f"- **Normalized MSE:** {(metrics['RMSE_Norm']**2):.4f}\n"
         f"- **Normalized MAE:** {metrics['MAE_Norm']:.4f}\n\n"
         "Note: normalized errors divide SECCHI residuals by `DEPTH_MAX_FEET`, so this is a depth-relative ratio.\n\n"
         "![TabNet Training Loss](28_tabnet_training_loss.png)"
        ),
        
        ("Feature Importances",
         "Because TabNet uses sequential attention, it is highly interpretable. Below is the global importance TabNet assigned to each feature when making its decisions:\n\n"
         f"{df_to_markdown_table(imp_df.head(15))}\n\n"
         "![TabNet Importances](28_tabnet_importances.png)"
        ),
        
        ("Interpretations",
         "### TabNet vs. Random Forest\n\n"
         "If TabNet outperforms the standard MLP (Experiment 27), it confirms that tabular-specific attention mechanisms are necessary for neural networks to process this heterogeneous water quality data.\n"
         "Comparing this directly to **Experiment 22 ($R^2$ ~0.66)** reveals whether Google's Tabular Deep Learning framework can actually beat a highly-tuned traditional Random Forest ensemble on chronological environmental forecasting."
        )
    ]
    
    report_path = write_markdown_report("28_tabnet_chrono.md", "Experiment 28: TabNet (Tabular Deep Learning)", sections)
    print(f"\nReport generated at {report_path}")

if __name__ == "__main__":
    main()
