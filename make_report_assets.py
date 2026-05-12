from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


OUT = Path(r"C:\Users\36992072854\rt_iot2022_orange_outputs")


def save_class_distribution_plot(classes: pd.DataFrame) -> None:
    plt.figure(figsize=(11, 6))
    plot_data = classes.sort_values("count", ascending=True)
    plt.barh(plot_data["Attack_type"], plot_data["count"])
    plt.xlabel("Quantidade de registros")
    plt.title("Distribuicao de classes - RT-IoT2022")
    plt.tight_layout()
    plt.savefig(OUT / "plot_class_distribution.png", dpi=160)
    plt.close()


def save_metrics_plot(metrics: pd.DataFrame) -> None:
    labels = metrics["feature_set"] + " / " + metrics["model"]
    plt.figure(figsize=(12, 6))
    plt.barh(labels, metrics["f1_weighted"])
    plt.xlabel("F1-score weighted")
    plt.xlim(0, 1.05)
    plt.title("Comparacao de modelos e conjuntos de features")
    plt.tight_layout()
    plt.savefig(OUT / "plot_model_f1_weighted.png", dpi=160)
    plt.close()


def save_top_features_plot(consensus: pd.DataFrame) -> None:
    top = consensus.head(20).sort_values("average_rank", ascending=False)
    plt.figure(figsize=(11, 7))
    plt.barh(top["feature"], top["average_rank"])
    plt.xlabel("Rank medio (menor e melhor)")
    plt.title("Top 20 features por consenso")
    plt.tight_layout()
    plt.savefig(OUT / "plot_top20_features_consensus.png", dpi=160)
    plt.close()


def save_confusion_plot() -> None:
    cm_path = OUT / "confusion_matrices" / "selected_top25_random_forest.csv"
    cm = pd.read_csv(cm_path, index_col=0)
    labels = [c.removeprefix("pred_") for c in cm.columns]

    plt.figure(figsize=(10, 8))
    plt.imshow(cm.values, cmap="Blues")
    plt.title("Matriz de confusao - Random Forest / Top 25")
    plt.xticks(range(len(labels)), labels, rotation=90)
    plt.yticks(range(len(labels)), labels)
    plt.colorbar(label="Registros")
    plt.tight_layout()
    plt.savefig(OUT / "plot_confusion_matrix_random_forest_top25.png", dpi=160)
    plt.close()


def write_technical_report(
    classes: pd.DataFrame,
    metrics: pd.DataFrame,
    consensus: pd.DataFrame,
    selected_features: list[str],
) -> None:
    best = metrics.iloc[0]
    all_rf = metrics[(metrics["feature_set"] == "all_features") & (metrics["model"] == "Random Forest")].iloc[0]
    selected_rf = metrics[(metrics["feature_set"] == "selected_top25") & (metrics["model"] == "Random Forest")].iloc[0]
    report = f"""# Relatorio tecnico - Deteccao de ataques IoT com RT-IoT2022

## 1. Preparacao dos dados

A base RT-IoT2022 foi copiada para uma pasta estavel e salva como `RT_IOT2022.csv`. Em seguida, foi gerada a versao limpa `RT_IOT2022_prepared.csv`, removendo a primeira coluna de indice exportada no CSV original. A variavel alvo usada na classificacao foi `Attack_type`.

O conjunto final possui 123117 registros, 84 colunas apos a remocao do indice, 81 atributos numericos e duas variaveis categoricas (`proto` e `service`). Nao foram identificados valores ausentes no dataset.

Distribuicao das classes:

```
{classes.to_string(index=False)}
```

Observa-se forte desbalanceamento: `DOS_SYN_Hping` representa aproximadamente 76,89% da base, enquanto `Metasploit_Brute_Force_SSH` e `NMAP_FIN_SCAN` possuem poucas dezenas de exemplos.

## 2. Selecao de features

Foram aplicadas tres estrategias de ranqueamento: Information Gain aproximado por mutual information, Chi-Square e ReliefF. Como criterio final, foi usada a media dos ranks dos tres metodos, selecionando as 25 melhores features.

Top 25 features selecionadas:

```
{chr(10).join(selected_features)}
```

Top 20 por consenso:

```
{consensus.head(20).to_string(index=False)}
```

A reducao dimensional gerou o arquivo `RT_IOT2022_selected_top25.csv`, que pode ser carregado no Orange para repetir a comparacao com menos atributos.

## 3. Treinamento e avaliacao dos modelos

Foram treinados tres algoritmos de classificacao com validacao cruzada estratificada de 5 folds: Decision Tree, Random Forest e Naive Bayes. Cada algoritmo foi avaliado com todas as features e com as 25 features selecionadas.

Resumo das metricas:

```
{metrics.to_string(index=False)}
```

O melhor resultado foi obtido por `{best["model"]}` usando `{best["feature_set"]}`, com accuracy de {best["accuracy"]:.4f}, F1 weighted de {best["f1_weighted"]:.4f} e F1 macro de {best["f1_macro"]:.4f}.

## 4. Analise critica

O Random Forest apresentou o melhor desempenho geral. Esse resultado e coerente com dados tabulares de rede, pois o algoritmo consegue combinar muitas regras nao lineares e reduzir a instabilidade de uma unica arvore por meio do ensemble.

A selecao de features melhorou levemente o Random Forest: com todas as features o F1 weighted foi {all_rf["f1_weighted"]:.4f}, enquanto com as 25 selecionadas foi {selected_rf["f1_weighted"]:.4f}. A diferenca e pequena, mas indica que a remocao de atributos menos relevantes nao prejudicou o modelo e ainda reduziu dimensionalidade.

Os tipos de ataque mais dificeis foram as classes minoritarias. No melhor modelo, `Metasploit_Brute_Force_SSH` teve recall de 0,8108 e `NMAP_FIN_SCAN` teve recall de 0,8571. Isso ocorre principalmente porque ha poucos exemplos dessas classes para o modelo aprender padroes robustos.

Existe risco de overfitting principalmente na Decision Tree, pois arvores individuais podem memorizar padroes especificos do conjunto de treino. A validacao cruzada reduz esse risco na avaliacao. O Random Forest tende a ser mais robusto porque combina varias arvores e apresentou resultados estaveis tanto com todas as features quanto com o subconjunto selecionado.

## 5. Arquivos para anexar ou consultar

- `RT_IOT2022_prepared.csv`: dataset limpo para o Orange.
- `RT_IOT2022_selected_top25.csv`: dataset reduzido para comparacao.
- `feature_ranking_*.csv`: rankings de features.
- `model_metrics_summary.csv`: tabela de metricas.
- `classification_reports/`: precision, recall e F1 por classe.
- `confusion_matrices/`: matrizes de confusao.
- `plot_class_distribution.png`, `plot_model_f1_weighted.png`, `plot_top20_features_consensus.png`, `plot_confusion_matrix_random_forest_top25.png`: graficos para o relatorio.

## 6. Observacao sobre o Orange

Para gerar o `.ows`, abra o Orange e monte o fluxo com `File -> Select Columns -> Impute -> Rank -> Test and Score -> Confusion Matrix`, usando `RT_IOT2022_prepared.csv` e `RT_IOT2022_selected_top25.csv`. Este ambiente executou a parte analitica e gerou os dados/resultados, mas a exportacao real do `.ows` depende da interface grafica do Orange.
"""
    (OUT / "technical_report_draft.md").write_text(report, encoding="utf-8")


def write_orange_checklist() -> None:
    checklist = """# Checklist do fluxo no Orange

1. Abrir `RT_IOT2022_prepared.csv` no widget `File`.
2. Confirmar `Attack_type` como target/categorical.
3. Confirmar `proto` e `service` como categóricas.
4. Ligar `File -> Select Columns` e remover a coluna de índice se ela aparecer.
5. Ligar `Select Columns -> Impute`.
6. Ligar `Impute -> Rank` para Information Gain, Chi-Square e ReliefF.
7. Para o comparativo reduzido, abrir também `RT_IOT2022_selected_top25.csv`.
8. Ligar `Impute -> Test and Score`.
9. Conectar `Tree`, `Random Forest` e `Naive Bayes` ao `Test and Score`.
10. Usar validação cruzada estratificada de 5 folds.
11. Ligar `Test and Score -> Confusion Matrix`.
12. Salvar o projeto como `.ows`.
"""
    (OUT / "orange_workflow_checklist.md").write_text(checklist, encoding="utf-8")


def main() -> None:
    classes = pd.read_csv(OUT / "class_distribution.csv")
    metrics = pd.read_csv(OUT / "model_metrics_summary.csv")
    consensus = pd.read_csv(OUT / "feature_ranking_consensus.csv")
    selected_features = (OUT / "selected_features_top25.txt").read_text(encoding="utf-8").splitlines()

    save_class_distribution_plot(classes)
    save_metrics_plot(metrics)
    save_top_features_plot(consensus)
    save_confusion_plot()
    write_technical_report(classes, metrics, consensus, selected_features)
    write_orange_checklist()
    print("Report assets generated.")


if __name__ == "__main__":
    main()
