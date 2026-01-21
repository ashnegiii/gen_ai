# Evaluation Framework

This framework enables us to measure semantic text similarity. It uses [`BERTScore`](https://pypi.org/project/bert-score/) with the `roberta-large` model.

Before running the evaluation framework ensure the **backend** and **frontend** are **setup** and **running**.

1. Once the app is running upload FAQ documents of your choice (CSV files with format `(question,answer)`)

2. Configure environment variables by copying `.env.example` and calling it `.env`

3. Ensure that your `venv` is set to the one created for the app backend:

```bash
# Current location must be the project root directory

# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Run the evaluation script:

**Hint: Depending on your Python installation use either `python` or `python3` in the following command:**
```bash
# Current location must be the project root directory
python3 -m evaluation.evaluate_bertscore
```

4. Results can be found in the "**evaluation/results**" folder
