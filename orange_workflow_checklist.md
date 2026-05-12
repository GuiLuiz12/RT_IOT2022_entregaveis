# Checklist do fluxo no Orange

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
