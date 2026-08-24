def ingest_dataframe(
    df: pd.DataFrame,
    mode: str = "append",
    db: Session = None,
) -> dict[str, Any]:
    """
    Ingest delay data from DataFrame into database.
    
    Args:
        df: DataFrame with delay records
        mode: 'append' or 'replace'
        db: SQLAlchemy session
    
    Returns:
        Dictionary with ingestion stats
    
    Raises:
        ValueError: If data validation fails
        DatabaseError: If database operation fails
    """
    if df.empty:
        raise ValueError("Cannot ingest empty DataFrame")
    
    required_columns = {"shop_code", "agency_code", "durn", "eff_durn"}
    missing_cols = required_columns - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing_cols))}. "
            f"Expected columns: {', '.join(sorted(required_columns))}"
        )
    
    try:
        if mode == "replace":
            logger.warning("Replace mode: deleting all existing delay records")
            db.query(DelayEvent).delete()
            db.commit()
    except Exception as e:
        logger.error(f"Failed to clear data in replace mode: {str(e)}")
        db.rollback()
        raise ValueError(f"Database error during replace: {str(e)}")