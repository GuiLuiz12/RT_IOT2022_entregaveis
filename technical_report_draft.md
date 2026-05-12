# Relatorio tecnico - Deteccao de ataques IoT com RT-IoT2022

## 1. Preparacao dos dados

A base RT-IoT2022 foi copiada para uma pasta estavel e salva como `RT_IOT2022.csv`. Em seguida, foi gerada a versao limpa `RT_IOT2022_prepared.csv`, removendo a primeira coluna de indice exportada no CSV original. A variavel alvo usada na classificacao foi `Attack_type`.

O conjunto final possui 123117 registros, 84 colunas apos a remocao do indice, 81 atributos numericos e duas variaveis categoricas (`proto` e `service`). Nao foram identificados valores ausentes no dataset.

Distribuicao das classes:

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

Observa-se forte desbalanceamento: `DOS_SYN_Hping` representa aproximadamente 76,89% da base, enquanto `Metasploit_Brute_Force_SSH` e `NMAP_FIN_SCAN` possuem poucas dezenas de exemplos.

## 2. Selecao de features

Foram aplicadas tres estrategias de ranqueamento: Information Gain aproximado por mutual information, Chi-Square e ReliefF. Como criterio final, foi usada a media dos ranks dos tres metodos, selecionando as 25 melhores features.

Top 25 features selecionadas:

```
fwd_init_window_size
id.resp_p
fwd_last_window_size
fwd_pkts_payload.max
payload_bytes_per_second
fwd_pkts_per_sec
flow_pkts_per_sec
bwd_pkts_per_sec
flow_iat.max
fwd_pkts_payload.avg
service
fwd_pkts_payload.min
flow_pkts_payload.max
flow_pkts_payload.std
flow_pkts_payload.avg
flow_SYN_flag_count
fwd_iat.max
fwd_URG_flag_count
fwd_header_size_max
fwd_header_size_min
id.orig_p
flow_iat.avg
bwd_pkts_payload.max
bwd_pkts_payload.std
flow_FIN_flag_count
```

Top 20 por consenso:

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

A reducao dimensional gerou o arquivo `RT_IOT2022_selected_top25.csv`, que pode ser carregado no Orange para repetir a comparacao com menos atributos.

## 3. Treinamento e avaliacao dos modelos

Foram treinados tres algoritmos de classificacao com validacao cruzada estratificada de 5 folds: Decision Tree, Random Forest e Naive Bayes. Cada algoritmo foi avaliado com todas as features e com as 25 features selecionadas.

Resumo das metricas:

```
   feature_set         model  accuracy  precision_weighted  recall_weighted  f1_weighted  precision_macro  recall_macro  f1_macro
selected_top25 Random Forest  0.998432            0.998433         0.998432     0.998430         0.979065      0.965516  0.972021
  all_features Random Forest  0.998408            0.998405         0.998408     0.998404         0.974895      0.961163  0.967765
  all_features Decision Tree  0.997831            0.997847         0.997831     0.997837         0.955407      0.962605  0.958514
selected_top25 Decision Tree  0.997604            0.997604         0.997604     0.997604         0.964403      0.962967  0.963642
  all_features   Naive Bayes  0.801019            0.913166         0.801019     0.822824         0.461959      0.513103  0.384821
selected_top25   Naive Bayes  0.800353            0.897228         0.800353     0.821860         0.517259      0.530619  0.423899
```

O melhor resultado foi obtido por `Random Forest` usando `selected_top25`, com accuracy de 0.9984, F1 weighted de 0.9984 e F1 macro de 0.9720.

## 4. Analise critica

O Random Forest apresentou o melhor desempenho geral. Esse resultado e coerente com dados tabulares de rede, pois o algoritmo consegue combinar muitas regras nao lineares e reduzir a instabilidade de uma unica arvore por meio do ensemble.

A selecao de features melhorou levemente o Random Forest: com todas as features o F1 weighted foi 0.9984, enquanto com as 25 selecionadas foi 0.9984. A diferenca e pequena, mas indica que a remocao de atributos menos relevantes nao prejudicou o modelo e ainda reduziu dimensionalidade.

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
