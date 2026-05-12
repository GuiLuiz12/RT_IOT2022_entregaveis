# RT-IoT2022 - resultados para relatório

## Preparação dos dados
- Linhas analisadas: 123117.
- Colunas após remoção do índice: 84.
- A primeira coluna de índice foi removida e uma cópia estável foi salva como `RT_IOT2022_prepared.csv`.
- `Attack_type` foi usado como variável alvo multiclasse; `proto` e `service` foram tratados como categóricas.
- Valores ausentes foram tratados por imputação nos pipelines de modelagem.

## Distribuição de classes
```
               Attack_type  count  percent
             DOS_SYN_Hping  94659  76.8854
               Thing_Speak   8108   6.5856
            ARP_poisioning   7750   6.2948
              MQTT_Publish   4146   3.3675
             NMAP_UDP_SCAN   2590   2.1037
       NMAP_XMAS_TREE_SCAN   2010   1.6326
         NMAP_OS_DETECTION   2000   1.6245
             NMAP_TCP_scan   1002   0.8139
            DDOS_Slowloris    534   0.4337
                Wipro_bulb    253   0.2055
Metasploit_Brute_Force_SSH     37   0.0301
             NMAP_FIN_SCAN     28   0.0227
```

## Features selecionadas
- Critério usado: consenso entre Information Gain (aproximado por mutual information), Chi-Square e ReliefF.
- Top 25 selecionadas:
fwd_init_window_size, id.resp_p, fwd_last_window_size, fwd_pkts_payload.max, payload_bytes_per_second, fwd_pkts_per_sec, flow_pkts_per_sec, bwd_pkts_per_sec, flow_iat.max, fwd_pkts_payload.avg, service, fwd_pkts_payload.min, flow_pkts_payload.max, flow_pkts_payload.std, flow_pkts_payload.avg, flow_SYN_flag_count, fwd_iat.max, fwd_URG_flag_count, fwd_header_size_max, fwd_header_size_min, id.orig_p, flow_iat.avg, bwd_pkts_payload.max, bwd_pkts_payload.std, flow_FIN_flag_count

## Métricas principais
```
   feature_set         model  accuracy  precision_weighted  recall_weighted  f1_weighted  precision_macro  recall_macro  f1_macro
selected_top25 Random Forest  0.998432            0.998433         0.998432     0.998430         0.979065      0.965516  0.972021
  all_features Random Forest  0.998408            0.998405         0.998408     0.998404         0.974895      0.961163  0.967765
  all_features Decision Tree  0.997831            0.997847         0.997831     0.997837         0.955407      0.962605  0.958514
selected_top25 Decision Tree  0.997604            0.997604         0.997604     0.997604         0.964403      0.962967  0.963642
  all_features   Naive Bayes  0.801019            0.913166         0.801019     0.822824         0.461959      0.513103  0.384821
selected_top25   Naive Bayes  0.800353            0.897228         0.800353     0.821860         0.517259      0.530619  0.423899
```

## Comparação all features vs. top 25
- Melhor modelo geral: Random Forest com `selected_top25`.
- Accuracy: 0.9984; F1 weighted: 0.9984; Recall macro: 0.9655.
- Use `model_metrics_summary.csv` para preencher a tabela do relatório.

## Top 20 features por consenso
```
                 feature  information_gain_rank  chi_square_rank  relieff_rank  average_rank  selected_top_k
    fwd_init_window_size                     10                5             5      6.666667            True
               id.resp_p                      8                7             8      7.666667            True
    fwd_last_window_size                      9                3            17      9.666667            True
    fwd_pkts_payload.max                      2               34             6     14.000000            True
payload_bytes_per_second                     25               13             7     15.000000            True
        fwd_pkts_per_sec                     20               17            10     15.666667            True
       flow_pkts_per_sec                     21               16            11     16.000000            True
        bwd_pkts_per_sec                     22               15            13     16.666667            True
            flow_iat.max                     16               12            24     17.333333            True
    fwd_pkts_payload.avg                      1               39            12     17.333333            True
                 service                     53                2             1     18.666667            True
    fwd_pkts_payload.min                     13               30            15     19.333333            True
   flow_pkts_payload.max                      7               32            20     19.666667            True
   flow_pkts_payload.std                     11               36            14     20.333333            True
   flow_pkts_payload.avg                      6               45            16     22.333333            True
     flow_SYN_flag_count                     26               33             9     22.666667            True
             fwd_iat.max                     38               11            23     24.000000            True
      fwd_URG_flag_count                     72                1             2     25.000000            True
     fwd_header_size_max                     28               28            22     26.000000            True
     fwd_header_size_min                     30               31            21     27.333333            True
```

## Análise crítica sugerida
- O melhor algoritmo deve ser justificado principalmente por F1 e recall, não apenas accuracy, porque há desbalanceamento entre classes.
- Se Random Forest ficar em primeiro, a explicação provável é a capacidade de capturar relações não lineares e interações entre estatísticas de fluxo.
- Se a versão com top 25 mantiver métricas próximas da versão com todas as features, a seleção reduziu dimensionalidade sem perda relevante.
- Os ataques mais difíceis devem ser identificados pelas linhas com menor recall nos arquivos de `classification_reports/` e pelas confusões nas matrizes em `confusion_matrices/`.
- Há risco de overfitting principalmente em árvore única; a validação cruzada com 5 folds mitiga a avaliação otimista, e Random Forest tende a ser mais estável.

## Arquivos gerados
- `RT_IOT2022.csv`: cópia estável do CSV original.
- `RT_IOT2022_prepared.csv`: dados limpos para importar no Orange.
- `RT_IOT2022_selected_top25.csv`: versão com features selecionadas.
- `class_distribution.csv`, `missing_values.csv`, `numeric_summary.csv`: apoio à EDA.
- `feature_ranking_*.csv`: rankings de atributos.
- `model_metrics_summary.csv`: tabela final de comparação.
- `classification_reports/` e `confusion_matrices/`: métricas por classe e matrizes.

## Como montar no Orange
1. Use `File` com `RT_IOT2022_prepared.csv`.
2. Defina `Attack_type` como alvo, `proto` e `service` como categóricas.
3. Para comparar features selecionadas, use também `RT_IOT2022_selected_top25.csv`.
4. Ligue `File -> Impute -> Test and Score` com `Tree`, `Random Forest` e `Naive Bayes`.
5. Use `Confusion Matrix` a partir de `Test and Score` para os prints do relatório.