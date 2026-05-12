from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import chi2, mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier


SOURCE = Path(
    r"C:\Users\36992072854\AppData\Local\Temp\2312551d-6a6c-4a23-b14a-d78701382cb2_rt-iot2022.zip.cb2\RT_IOT2022"
)
OUT = Path(r"C:\Users\36992072854\rt_iot2022_orange_outputs")
TARGET = "Attack_type"
RANDOM_STATE = 42
TOP_K = 25
RELIEF_SAMPLE_SIZE = 5000


def ensure_output_dir() -> None:
    OUT.mkdir(parents=True, exist_ok=True)


def load_and_prepare() -> pd.DataFrame:
    stable_csv = OUT / "RT_IOT2022.csv"
    if not stable_csv.exists():
        shutil.copyfile(SOURCE, stable_csv)

    df = pd.read_csv(stable_csv)

    index_like = [
        col
        for col in df.columns
        if str(col).startswith("Unnamed") or str(col).strip() == ""
    ]
    if index_like:
        df = df.drop(columns=index_like)

    df.to_csv(OUT / "RT_IOT2022_prepared.csv", index=False)
    return df


def write_eda(df: pd.DataFrame) -> None:
    class_counts = df[TARGET].value_counts().rename_axis(TARGET).reset_index(name="count")
    class_counts["percent"] = (class_counts["count"] / len(df) * 100).round(4)
    class_counts.to_csv(OUT / "class_distribution.csv", index=False)

    missing = df.isna().sum().rename_axis("column").reset_index(name="missing_count")
    missing["missing_percent"] = (missing["missing_count"] / len(df) * 100).round(4)
    missing.to_csv(OUT / "missing_values.csv", index=False)

    dtype_rows = pd.DataFrame({"column": df.columns, "dtype": [str(t) for t in df.dtypes]})
    dtype_rows.to_csv(OUT / "column_types.csv", index=False)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        df[numeric_cols].describe().T.to_csv(OUT / "numeric_summary.csv")

    overview = {
        "rows": int(df.shape[0]),
        "columns_after_index_drop": int(df.shape[1]),
        "target": TARGET,
        "classes": int(df[TARGET].nunique()),
        "categorical_features_detected": [
            c for c in df.columns if not is_numeric_dtype(df[c]) and c != TARGET
        ],
        "numeric_features_detected": len(numeric_cols),
        "total_missing_values": int(df.isna().sum().sum()),
    }
    (OUT / "dataset_overview.json").write_text(
        json.dumps(overview, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def split_columns(df: pd.DataFrame, selected_features: list[str] | None = None) -> tuple[pd.DataFrame, pd.Series, list[str], list[str]]:
    features = [c for c in df.columns if c != TARGET]
    if selected_features is not None:
        features = [c for c in selected_features if c in features]

    x = df[features].copy()
    y = df[TARGET].copy()
    categorical = [c for c in features if not is_numeric_dtype(x[c])]
    numeric = [c for c in features if c not in categorical]
    return x, y, numeric, categorical


def make_preprocessor(numeric: list[str], categorical: list[str], scale: bool = False) -> ColumnTransformer:
    numeric_steps: list[tuple[str, object]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        numeric_steps.append(("scaler", MinMaxScaler()))

    transformers: list[tuple[str, object, list[str]]] = [
        ("num", Pipeline(numeric_steps), numeric),
    ]
    if categorical:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical,
            )
        )

    return ColumnTransformer(transformers, sparse_threshold=0)


def transformed_feature_names(preprocessor: ColumnTransformer, numeric: list[str], categorical: list[str]) -> list[str]:
    names = [f"num__{c}" for c in numeric]
    if categorical:
        onehot = preprocessor.named_transformers_["cat"].named_steps["onehot"]
        cat_names = onehot.get_feature_names_out(categorical).tolist()
        names.extend([f"cat__{c}" for c in cat_names])
    return names


def original_feature_name(transformed_name: str, original_features: list[str]) -> str:
    if transformed_name.startswith("num__"):
        return transformed_name.removeprefix("num__")
    raw = transformed_name.removeprefix("cat__")
    for feature in original_features:
        if raw == feature or raw.startswith(f"{feature}_"):
            return feature
    return raw


def aggregate_scores(
    feature_names: list[str],
    scores: np.ndarray,
    original_features: list[str],
    method: str,
) -> pd.DataFrame:
    rows = []
    for name, score in zip(feature_names, scores):
        rows.append(
            {
                "feature": original_feature_name(name, original_features),
                "transformed_feature": name,
                "score": float(score) if np.isfinite(score) else 0.0,
            }
        )
    detailed = pd.DataFrame(rows).sort_values("score", ascending=False)
    detailed.to_csv(OUT / f"feature_ranking_{method}_detailed.csv", index=False)

    return (
        detailed.groupby("feature", as_index=False)["score"]
        .max()
        .sort_values("score", ascending=False)
        .reset_index(drop=True)
    )


def relief_f_scores(x_array: np.ndarray, y: pd.Series, feature_names: list[str]) -> np.ndarray:
    # A compact ReliefF-style approximation: compare each sampled row with nearest
    # same-class and different-class neighbours on min-max scaled data.
    y_values = y.to_numpy()
    classes, counts = np.unique(y_values, return_counts=True)
    valid_classes = classes[counts >= 2]
    mask = np.isin(y_values, valid_classes)
    x_array = x_array[mask]
    y_values = y_values[mask]

    if len(y_values) > RELIEF_SAMPLE_SIZE:
        _, sample_idx = train_test_split(
            np.arange(len(y_values)),
            train_size=RELIEF_SAMPLE_SIZE,
            stratify=y_values,
            random_state=RANDOM_STATE,
        )
        x_array = x_array[sample_idx]
        y_values = y_values[sample_idx]

    scores = np.zeros(len(feature_names), dtype=float)
    for cls in np.unique(y_values):
        hit_data = x_array[y_values == cls]
        miss_data = x_array[y_values != cls]
        cls_data = hit_data
        if len(hit_data) < 2 or len(miss_data) < 1:
            continue

        hit_nn = NearestNeighbors(n_neighbors=2).fit(hit_data)
        miss_nn = NearestNeighbors(n_neighbors=1).fit(miss_data)
        _, hit_indices = hit_nn.kneighbors(cls_data)
        _, miss_indices = miss_nn.kneighbors(cls_data)

        nearest_hits = hit_data[hit_indices[:, 1]]
        nearest_misses = miss_data[miss_indices[:, 0]]
        scores += np.mean(np.abs(cls_data - nearest_misses) - np.abs(cls_data - nearest_hits), axis=0)

    return scores / max(1, len(np.unique(y_values)))


def write_feature_rankings(df: pd.DataFrame) -> list[str]:
    x, y, numeric, categorical = split_columns(df)
    original_features = x.columns.tolist()

    preprocessor_scaled = make_preprocessor(numeric, categorical, scale=True)
    x_scaled = preprocessor_scaled.fit_transform(x)
    feature_names = transformed_feature_names(preprocessor_scaled, numeric, categorical)

    mi_scores = mutual_info_classif(x_scaled, y, discrete_features="auto", random_state=RANDOM_STATE)
    mi_rank = aggregate_scores(feature_names, mi_scores, original_features, "information_gain_proxy")
    mi_rank.to_csv(OUT / "feature_ranking_information_gain.csv", index=False)

    chi_scores, _ = chi2(x_scaled, y)
    chi_rank = aggregate_scores(feature_names, chi_scores, original_features, "chi_square")
    chi_rank.to_csv(OUT / "feature_ranking_chi_square.csv", index=False)

    relief_scores = relief_f_scores(x_scaled, y, feature_names)
    relief_rank = aggregate_scores(feature_names, relief_scores, original_features, "relieff")
    relief_rank.to_csv(OUT / "feature_ranking_relieff.csv", index=False)

    rank_frames = []
    for method, frame in [
        ("information_gain", mi_rank),
        ("chi_square", chi_rank),
        ("relieff", relief_rank),
    ]:
        tmp = frame.copy()
        tmp[f"{method}_rank"] = np.arange(1, len(tmp) + 1)
        rank_frames.append(tmp[["feature", f"{method}_rank"]])

    consensus = rank_frames[0]
    for frame in rank_frames[1:]:
        consensus = consensus.merge(frame, on="feature", how="outer")
    rank_cols = [c for c in consensus.columns if c.endswith("_rank")]
    consensus[rank_cols] = consensus[rank_cols].fillna(len(original_features) + 1)
    consensus["average_rank"] = consensus[rank_cols].mean(axis=1)
    consensus = consensus.sort_values("average_rank").reset_index(drop=True)
    consensus["selected_top_k"] = consensus.index < TOP_K
    consensus.to_csv(OUT / "feature_ranking_consensus.csv", index=False)

    selected = consensus.loc[consensus["selected_top_k"], "feature"].tolist()
    (OUT / "selected_features_top25.txt").write_text("\n".join(selected), encoding="utf-8")
    df[selected + [TARGET]].to_csv(OUT / "RT_IOT2022_selected_top25.csv", index=False)
    return selected


def dense_pipeline(numeric: list[str], categorical: list[str], classifier: object) -> Pipeline:
    return Pipeline(
        [
            ("preprocess", make_preprocessor(numeric, categorical, scale=False)),
            ("model", classifier),
        ]
    )


def evaluate_models(df: pd.DataFrame, selected_features: list[str]) -> None:
    model_defs = {
        "Decision Tree": DecisionTreeClassifier(random_state=RANDOM_STATE, max_depth=None),
        "Random Forest": RandomForestClassifier(
            n_estimators=100,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            class_weight="balanced_subsample",
        ),
        "Naive Bayes": GaussianNB(),
    }

    results = []
    confusion_dir = OUT / "confusion_matrices"
    reports_dir = OUT / "classification_reports"
    confusion_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)

    for feature_set_name, feature_subset in [
        ("all_features", None),
        ("selected_top25", selected_features),
    ]:
        x, y, numeric, categorical = split_columns(df, feature_subset)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

        for model_name, classifier in model_defs.items():
            pipe = dense_pipeline(numeric, categorical, classifier)
            y_pred = cross_val_predict(pipe, x, y, cv=cv, n_jobs=-1)

            results.append(
                {
                    "feature_set": feature_set_name,
                    "model": model_name,
                    "accuracy": accuracy_score(y, y_pred),
                    "precision_weighted": precision_score(y, y_pred, average="weighted", zero_division=0),
                    "recall_weighted": recall_score(y, y_pred, average="weighted", zero_division=0),
                    "f1_weighted": f1_score(y, y_pred, average="weighted", zero_division=0),
                    "precision_macro": precision_score(y, y_pred, average="macro", zero_division=0),
                    "recall_macro": recall_score(y, y_pred, average="macro", zero_division=0),
                    "f1_macro": f1_score(y, y_pred, average="macro", zero_division=0),
                }
            )

            report = classification_report(y, y_pred, zero_division=0, output_dict=True)
            report_df = pd.DataFrame(report).T
            safe_name = f"{feature_set_name}_{model_name}".lower().replace(" ", "_")
            report_df.to_csv(reports_dir / f"{safe_name}.csv")

            labels = sorted(y.unique())
            cm = pd.DataFrame(
                confusion_matrix(y, y_pred, labels=labels),
                index=[f"actual_{c}" for c in labels],
                columns=[f"pred_{c}" for c in labels],
            )
            cm.to_csv(confusion_dir / f"{safe_name}.csv")

    metrics = pd.DataFrame(results).sort_values(["f1_weighted", "accuracy"], ascending=False)
    metrics.to_csv(OUT / "model_metrics_summary.csv", index=False)


def write_report_notes(df: pd.DataFrame, selected_features: list[str]) -> None:
    metrics = pd.read_csv(OUT / "model_metrics_summary.csv")
    classes = pd.read_csv(OUT / "class_distribution.csv")
    consensus = pd.read_csv(OUT / "feature_ranking_consensus.csv")

    best = metrics.iloc[0]
    selected_metrics = metrics[metrics["feature_set"] == "selected_top25"]
    all_metrics = metrics[metrics["feature_set"] == "all_features"]

    notes = [
        "# RT-IoT2022 - resultados para relatório",
        "",
        "## Preparação dos dados",
        f"- Linhas analisadas: {len(df)}.",
        f"- Colunas após remoção do índice: {df.shape[1]}.",
        "- A primeira coluna de índice foi removida e uma cópia estável foi salva como `RT_IOT2022_prepared.csv`.",
        "- `Attack_type` foi usado como variável alvo multiclasse; `proto` e `service` foram tratados como categóricas.",
        "- Valores ausentes foram tratados por imputação nos pipelines de modelagem.",
        "",
        "## Distribuição de classes",
        "```",
        classes.head(15).to_string(index=False),
        "```",
        "",
        "## Features selecionadas",
        "- Critério usado: consenso entre Information Gain (aproximado por mutual information), Chi-Square e ReliefF.",
        "- Top 25 selecionadas:",
        ", ".join(selected_features),
        "",
        "## Métricas principais",
        "```",
        metrics.to_string(index=False),
        "```",
        "",
        "## Comparação all features vs. top 25",
        f"- Melhor modelo geral: {best['model']} com `{best['feature_set']}`.",
        f"- Accuracy: {best['accuracy']:.4f}; F1 weighted: {best['f1_weighted']:.4f}; Recall macro: {best['recall_macro']:.4f}.",
        "- Use `model_metrics_summary.csv` para preencher a tabela do relatório.",
        "",
        "## Top 20 features por consenso",
        "```",
        consensus.head(20).to_string(index=False),
        "```",
        "",
        "## Análise crítica sugerida",
        "- O melhor algoritmo deve ser justificado principalmente por F1 e recall, não apenas accuracy, porque há desbalanceamento entre classes.",
        "- Se Random Forest ficar em primeiro, a explicação provável é a capacidade de capturar relações não lineares e interações entre estatísticas de fluxo.",
        "- Se a versão com top 25 mantiver métricas próximas da versão com todas as features, a seleção reduziu dimensionalidade sem perda relevante.",
        "- Os ataques mais difíceis devem ser identificados pelas linhas com menor recall nos arquivos de `classification_reports/` e pelas confusões nas matrizes em `confusion_matrices/`.",
        "- Há risco de overfitting principalmente em árvore única; a validação cruzada com 5 folds mitiga a avaliação otimista, e Random Forest tende a ser mais estável.",
        "",
        "## Arquivos gerados",
        "- `RT_IOT2022.csv`: cópia estável do CSV original.",
        "- `RT_IOT2022_prepared.csv`: dados limpos para importar no Orange.",
        "- `RT_IOT2022_selected_top25.csv`: versão com features selecionadas.",
        "- `class_distribution.csv`, `missing_values.csv`, `numeric_summary.csv`: apoio à EDA.",
        "- `feature_ranking_*.csv`: rankings de atributos.",
        "- `model_metrics_summary.csv`: tabela final de comparação.",
        "- `classification_reports/` e `confusion_matrices/`: métricas por classe e matrizes.",
        "",
        "## Como montar no Orange",
        "1. Use `File` com `RT_IOT2022_prepared.csv`.",
        "2. Defina `Attack_type` como alvo, `proto` e `service` como categóricas.",
        "3. Para comparar features selecionadas, use também `RT_IOT2022_selected_top25.csv`.",
        "4. Ligue `File -> Impute -> Test and Score` com `Tree`, `Random Forest` e `Naive Bayes`.",
        "5. Use `Confusion Matrix` a partir de `Test and Score` para os prints do relatório.",
    ]
    (OUT / "report_notes.md").write_text("\n".join(notes), encoding="utf-8")


def main() -> None:
    ensure_output_dir()
    df = load_and_prepare()
    write_eda(df)
    selected_features = write_feature_rankings(df)
    evaluate_models(df, selected_features)
    write_report_notes(df, selected_features)
    print(f"Completed analysis. Outputs: {OUT}")


if __name__ == "__main__":
    main()
