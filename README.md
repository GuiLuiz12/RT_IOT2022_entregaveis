# Relatório Técnico - Detecção de Ataques com Machine Learning no RT-IoT2022

## 1. Introdução

Este relatório apresenta o desenvolvimento, treinamento e avaliação de modelos de Machine Learning para detecção de ataques em tráfego de rede IoT usando a base RT-IoT2022. O objetivo foi identificar diferentes classes de tráfego malicioso e legítimo, aplicar seleção de atributos e comparar algoritmos de classificação, conforme o escopo da atividade prática.

O trabalho foi executado de acordo com o plano original. Além do fluxo previsto para Orange Data Mining, foram gerados arquivos de apoio com os resultados analíticos para facilitar a construção do relatório final e a reprodução dos testes no Orange.

## 2. Arquivos Gerados

Todos os arquivos gerados estão em:

`C:\Users\36992072854\rt_iot2022_orange_outputs`

Principais evidências geradas:

- `RT_IOT2022.csv`: cópia estável do arquivo original, agora com extensão `.csv`.
- `RT_IOT2022_prepared.csv`: dataset preparado para importação no Orange.
- `RT_IOT2022_selected_top25.csv`: dataset reduzido com as 25 features selecionadas.
- `dataset_overview.json`: resumo estrutural da base.
- `class_distribution.csv`: distribuição das classes.
- `missing_values.csv`: verificação de valores ausentes.
- `feature_ranking_information_gain.csv`: ranking por Information Gain aproximado.
- `feature_ranking_chi_square.csv`: ranking por Chi-Square.
- `feature_ranking_relieff.csv`: ranking por ReliefF.
- `feature_ranking_consensus.csv`: ranking final por consenso.
- `model_metrics_summary.csv`: comparação final dos modelos.
- `classification_reports/`: precision, recall e F1-score por classe.
- `confusion_matrices/`: matrizes de confusão.
- `plot_class_distribution.png`: gráfico da distribuição de classes.
- `plot_model_f1_weighted.png`: gráfico comparativo dos modelos.
- `plot_top20_features_consensus.png`: gráfico das principais features.
- `plot_confusion_matrix_random_forest_top25.png`: matriz de confusão visual do melhor modelo.
- `orange_workflow_checklist.md`: checklist para montar o fluxo e salvar o `.ows` no Orange.

## 3. Preparação dos Dados

A base original estava em:

`C:\Users\36992072854\AppData\Local\Temp\2312551d-6a6c-4a23-b14a-d78701382cb2_rt-iot2022.zip.cb2\RT_IOT2022`

Como o arquivo não possuía extensão, foi aplicada a estratégia de fallback definida no plano: o arquivo foi copiado para uma pasta estável e salvo como `RT_IOT2022.csv`. Em seguida, foi gerada a versão preparada `RT_IOT2022_prepared.csv`.

Durante a preparação, a primeira coluna de índice exportada no CSV foi removida, pois não representa uma característica de tráfego de rede. A variável alvo definida foi `Attack_type`.

Resumo da base após preparação:

| Item | Valor |
|---|---:|
| Registros | 123117 |
| Colunas após remoção do índice | 84 |
| Variável alvo | Attack_type |
| Número de classes | 12 |
| Features numéricas | 81 |
| Features categóricas | 2 (`proto`, `service`) |
| Valores ausentes | 0 |

Evidência: `dataset_overview.json` e `missing_values.csv`.

## 4. Análise Exploratória

A base apresenta forte desbalanceamento entre as classes. A classe `DOS_SYN_Hping` representa a maior parte dos registros, enquanto `Metasploit_Brute_Force_SSH` e `NMAP_FIN_SCAN` possuem poucos exemplos.

Distribuição de classes:

| Classe | Registros | Percentual |
|---|---:|---:|
| DOS_SYN_Hping | 94659 | 76.8854% |
| Thing_Speak | 8108 | 6.5856% |
| ARP_poisioning | 7750 | 6.2948% |
| MQTT_Publish | 4146 | 3.3675% |
| NMAP_UDP_SCAN | 2590 | 2.1037% |
| NMAP_XMAS_TREE_SCAN | 2010 | 1.6326% |
| NMAP_OS_DETECTION | 2000 | 1.6245% |
| NMAP_TCP_scan | 1002 | 0.8139% |
| DDOS_Slowloris | 534 | 0.4337% |
| Wipro_bulb | 253 | 0.2055% |
| Metasploit_Brute_Force_SSH | 37 | 0.0301% |
| NMAP_FIN_SCAN | 28 | 0.0227% |

Evidências:

- Dados tabulares: `class_distribution.csv`
- Gráfico: `plot_class_distribution.png`

## 5. Tratamento de Inconsistências

Não foram encontrados valores ausentes na base. Mesmo assim, os pipelines de modelagem incluíram imputação como medida de segurança:

- Atributos numéricos: mediana.
- Atributos categóricos: valor mais frequente.

As colunas `proto` e `service` foram tratadas como categóricas. As demais features foram tratadas como numéricas.

Para uso no Orange, a configuração recomendada é:

- `Attack_type`: target/categorical.
- `proto`: categorical.
- `service`: categorical.
- Demais colunas: numeric.

## 6. Seleção de Features

Foram aplicadas três técnicas de seleção de atributos:

- Information Gain, aproximado por mutual information.
- Chi-Square.
- ReliefF.

Como critério final, foi construído um ranking por consenso usando a média dos ranks das três técnicas. Foram selecionadas as 25 melhores features para comparar o desempenho com o conjunto completo.

Top 25 features selecionadas:

| Ordem | Feature |
|---:|---|
| 1 | fwd_init_window_size |
| 2 | id.resp_p |
| 3 | fwd_last_window_size |
| 4 | fwd_pkts_payload.max |
| 5 | payload_bytes_per_second |
| 6 | fwd_pkts_per_sec |
| 7 | flow_pkts_per_sec |
| 8 | bwd_pkts_per_sec |
| 9 | flow_iat.max |
| 10 | fwd_pkts_payload.avg |
| 11 | service |
| 12 | fwd_pkts_payload.min |
| 13 | flow_pkts_payload.max |
| 14 | flow_pkts_payload.std |
| 15 | flow_pkts_payload.avg |
| 16 | flow_SYN_flag_count |
| 17 | fwd_iat.max |
| 18 | fwd_URG_flag_count |
| 19 | fwd_header_size_max |
| 20 | fwd_header_size_min |
| 21 | id.orig_p |
| 22 | flow_iat.avg |
| 23 | bwd_pkts_payload.max |
| 24 | bwd_pkts_payload.std |
| 25 | flow_FIN_flag_count |

Top 10 por consenso:

| Feature | Rank Information Gain | Rank Chi-Square | Rank ReliefF | Rank médio |
|---|---:|---:|---:|---:|
| fwd_init_window_size | 10 | 5 | 5 | 6.6667 |
| id.resp_p | 8 | 7 | 8 | 7.6667 |
| fwd_last_window_size | 9 | 3 | 17 | 9.6667 |
| fwd_pkts_payload.max | 2 | 34 | 6 | 14.0000 |
| payload_bytes_per_second | 25 | 13 | 7 | 15.0000 |
| fwd_pkts_per_sec | 20 | 17 | 10 | 15.6667 |
| flow_pkts_per_sec | 21 | 16 | 11 | 16.0000 |
| bwd_pkts_per_sec | 22 | 15 | 13 | 16.6667 |
| flow_iat.max | 16 | 12 | 24 | 17.3333 |
| fwd_pkts_payload.avg | 1 | 39 | 12 | 17.3333 |

Evidências:

- `feature_ranking_information_gain.csv`
- `feature_ranking_chi_square.csv`
- `feature_ranking_relieff.csv`
- `feature_ranking_consensus.csv`
- `selected_features_top25.txt`
- `plot_top20_features_consensus.png`

## 7. Treinamento dos Modelos

Foram treinados três algoritmos de classificação:

- Decision Tree.
- Random Forest.
- Naive Bayes.

Cada modelo foi avaliado em dois cenários:

- `all_features`: dataset com todas as features após preparação.
- `selected_top25`: dataset com as 25 features selecionadas.

A avaliação foi realizada com validação cruzada estratificada de 5 folds, mantendo a distribuição das classes em cada partição. Foram usadas as métricas:

- Accuracy.
- Precision weighted.
- Recall weighted.
- F1-score weighted.
- Precision macro.
- Recall macro.
- F1-score macro.

## 8. Resultados dos Modelos

Resumo das métricas:

| Conjunto | Modelo | Accuracy | Precision weighted | Recall weighted | F1 weighted | Precision macro | Recall macro | F1 macro |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| selected_top25 | Random Forest | 0.998432 | 0.998433 | 0.998432 | 0.998430 | 0.979065 | 0.965516 | 0.972021 |
| all_features | Random Forest | 0.998408 | 0.998405 | 0.998408 | 0.998404 | 0.974895 | 0.961163 | 0.967765 |
| all_features | Decision Tree | 0.997831 | 0.997847 | 0.997831 | 0.997837 | 0.955407 | 0.962605 | 0.958514 |
| selected_top25 | Decision Tree | 0.997604 | 0.997604 | 0.997604 | 0.997604 | 0.964403 | 0.962967 | 0.963642 |
| all_features | Naive Bayes | 0.801019 | 0.913166 | 0.801019 | 0.822824 | 0.461959 | 0.513103 | 0.384821 |
| selected_top25 | Naive Bayes | 0.800353 | 0.897228 | 0.800353 | 0.821860 | 0.517259 | 0.530619 | 0.423899 |

Evidências:

- `model_metrics_summary.csv`
- `plot_model_f1_weighted.png`

## 9. Melhor Modelo

O melhor modelo foi:

| Critério | Resultado |
|---|---|
| Modelo | Random Forest |
| Conjunto de features | selected_top25 |
| Accuracy | 0.998432 |
| Precision weighted | 0.998433 |
| Recall weighted | 0.998432 |
| F1 weighted | 0.998430 |
| F1 macro | 0.972021 |

O Random Forest apresentou melhor desempenho porque é adequado para dados tabulares com relações não lineares entre atributos. Como combina várias árvores, tende a ser mais robusto que uma Decision Tree isolada e menos sensível a ruído.

## 10. Matriz de Confusão e Desempenho por Classe

No melhor modelo, a maioria das classes apresentou recall muito alto. As classes majoritárias e intermediárias tiveram excelente desempenho.

Desempenho por classe do Random Forest com top 25 features:

| Classe | Precision | Recall | F1-score | Suporte |
|---|---:|---:|---:|---:|
| ARP_poisioning | 0.985672 | 0.994194 | 0.989915 | 7750 |
| DDOS_Slowloris | 0.988679 | 0.981273 | 0.984962 | 534 |
| DOS_SYN_Hping | 1.000000 | 1.000000 | 1.000000 | 94659 |
| MQTT_Publish | 1.000000 | 0.998794 | 0.999397 | 4146 |
| Metasploit_Brute_Force_SSH | 0.909091 | 0.810811 | 0.857143 | 37 |
| NMAP_FIN_SCAN | 0.888889 | 0.857143 | 0.872727 | 28 |
| NMAP_OS_DETECTION | 1.000000 | 1.000000 | 1.000000 | 2000 |
| NMAP_TCP_scan | 1.000000 | 0.998004 | 0.999001 | 1002 |
| NMAP_UDP_SCAN | 0.995726 | 0.989575 | 0.992641 | 2590 |
| NMAP_XMAS_TREE_SCAN | 0.999502 | 0.998010 | 0.998755 | 2010 |
| Thing_Speak | 0.993318 | 0.990010 | 0.991661 | 8108 |
| Wipro_bulb | 0.987903 | 0.968379 | 0.978044 | 253 |

Principais erros observados na matriz de confusão:

- `ARP_poisioning`: 41 registros foram classificados como `Thing_Speak`.
- `Thing_Speak`: 76 registros foram classificados como `ARP_poisioning`.
- `Metasploit_Brute_Force_SSH`: 4 registros foram classificados como `NMAP_UDP_SCAN` e 3 como `ARP_poisioning`.
- `NMAP_FIN_SCAN`: 3 registros foram classificados como `ARP_poisioning` e 1 como `Thing_Speak`.
- `Wipro_bulb`: 5 registros foram classificados como `Thing_Speak`.

Evidências:

- `classification_reports/selected_top25_random_forest.csv`
- `confusion_matrices/selected_top25_random_forest.csv`
- `plot_confusion_matrix_random_forest_top25.png`

## 11. Comparação: Todas as Features vs. Features Selecionadas

A seleção de features melhorou levemente o Random Forest:

| Cenário | Accuracy | F1 weighted | F1 macro |
|---|---:|---:|---:|
| Random Forest com todas as features | 0.998408 | 0.998404 | 0.967765 |
| Random Forest com top 25 features | 0.998432 | 0.998430 | 0.972021 |

A diferença é pequena, mas positiva. Isso indica que a redução de dimensionalidade manteve as informações relevantes e removeu atributos menos úteis. Além disso, a versão com 25 features simplifica o modelo e reduz o custo de processamento, o que é importante em cenários de detecção em tráfego IoT.

Para Decision Tree, a versão com todas as features teve F1 weighted ligeiramente maior, mas a versão reduzida teve F1 macro maior. Isso sugere que a seleção de features pode ajudar no equilíbrio entre classes, mesmo quando a métrica global weighted não melhora.

Para Naive Bayes, o desempenho geral foi inferior nos dois cenários. O F1 weighted ficou em torno de 0.82, bem abaixo dos modelos baseados em árvore. Isso é coerente com a hipótese de independência do Naive Bayes, que tende a ser fraca em atributos de tráfego de rede altamente correlacionados.

## 12. Ataques Mais Difíceis de Detectar

Os ataques mais difíceis foram:

- `Metasploit_Brute_Force_SSH`: recall 0.810811, suporte 37.
- `NMAP_FIN_SCAN`: recall 0.857143, suporte 28.
- `Wipro_bulb`: recall 0.968379, suporte 253.

A principal causa é o desbalanceamento da base. Classes com poucos exemplos têm menor representatividade no treinamento, o que torna mais difícil aprender padrões estáveis. Isso também explica por que métricas macro são importantes: elas reduzem a influência da classe dominante `DOS_SYN_Hping`.

## 13. Risco de Overfitting

Existe risco de overfitting, principalmente na Decision Tree, pois uma árvore única pode criar regras muito específicas para o conjunto de treino. Esse risco foi mitigado por:

- Validação cruzada estratificada de 5 folds.
- Comparação com Random Forest, que reduz variância ao combinar múltiplas árvores.
- Avaliação por métricas macro e weighted.
- Comparação entre dataset completo e dataset reduzido.

O Random Forest apresentou resultados muito próximos nos dois cenários, com todas as features e com top 25 features. Isso sugere boa estabilidade e menor risco de que o resultado dependa apenas de ruído em atributos específicos.

Ainda assim, como a base é muito desbalanceada, recomenda-se cautela ao interpretar apenas accuracy. O modelo acerta muito a classe majoritária, mas as classes raras continuam sendo o principal ponto de atenção.

## 14. Como Reproduzir no Orange

Para gerar o projeto `.ows`, use o arquivo `RT_IOT2022_prepared.csv` e monte o fluxo:

1. `File`: carregar `RT_IOT2022_prepared.csv`.
2. Confirmar `Attack_type` como target.
3. Confirmar `proto` e `service` como categóricas.
4. `Select Columns`: remover coluna de índice se ela aparecer.
5. `Impute`: manter imputação por mediana/moda.
6. `Rank`: executar Information Gain, Chi-Square e ReliefF.
7. `Test and Score`: usar validação cruzada estratificada de 5 folds.
8. Conectar os modelos `Tree`, `Random Forest` e `Naive Bayes`.
9. `Confusion Matrix`: gerar a matriz de confusão do melhor modelo.
10. Para comparação com features selecionadas, carregar também `RT_IOT2022_selected_top25.csv`.

Evidência auxiliar:

- `orange_workflow_checklist.md`

## 15. Conclusão

O escopo original foi concluído. A base RT-IoT2022 foi preparada, analisada, reduzida por seleção de features, usada no treinamento de três algoritmos e avaliada com métricas adequadas.

O melhor desempenho foi obtido pelo Random Forest com as 25 features selecionadas, alcançando accuracy de 0.998432 e F1 weighted de 0.998430. A seleção de features não prejudicou o modelo; pelo contrário, melhorou levemente as métricas do Random Forest e reduziu a dimensionalidade.

As classes mais difíceis foram as menos representadas, especialmente `Metasploit_Brute_Force_SSH` e `NMAP_FIN_SCAN`. Para trabalhos futuros, recomenda-se aplicar técnicas de balanceamento, como oversampling ou ajuste de pesos por classe, e comparar os resultados com os obtidos neste relatório.
