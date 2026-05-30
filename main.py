from src.ingestion.pipeline import run_mock_pipeline


def main() -> None:
    frame = run_mock_pipeline()
    print(f"CivicPulse pipeline generated {len(frame)} records.")
    print("Run `streamlit run app.py` to open the dashboard.")


if __name__ == "__main__":
    main()
