//! The numbers on the side cards of `/today`.
//!
//! Other features fill these in: the Flashcards module (#19) and the Error log (#21) own their
//! tables. Until those tables exist both functions answer 0, so this page never has to change.
//! To plug in a real count, replace the body of the function (keep the signature).

use renox::prelude::*;

/// Does a table exist (SQLite)?
async fn table_exists(db: &Db, name: &str) -> Result<bool> {
    let n: i64 =
        renox::db::sql("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = ?")
            .bind(name)
            .scalar(db)
            .await?;
    Ok(n > 0)
}

/// Flashcards due for the student today. EXTENSION POINT for #19: once `card_states` exists
/// this counts its rows with `due_on <= today`.
pub async fn flashcards_due(db: &Db, user_id: i64) -> Result<i64> {
    if !table_exists(db, "card_states").await? {
        return Ok(0);
    }
    Ok(
        renox::db::sql("SELECT COUNT(*) FROM card_states WHERE user_id = ? AND due_on <= ?")
            .bind(user_id)
            .bind(crate::clock::today().to_string())
            .scalar(db)
            .await?,
    )
}

/// Error log entries due for the student today. EXTENSION POINT for #21: once `error_entries`
/// exists this counts the unresolved rows with `due_on <= today`.
pub async fn errors_due(db: &Db, user_id: i64) -> Result<i64> {
    if !table_exists(db, "error_entries").await? {
        return Ok(0);
    }
    Ok(renox::db::sql(
        "SELECT COUNT(*) FROM error_entries WHERE user_id = ? AND resolved_at IS NULL AND due_on <= ?",
    )
    .bind(user_id)
    .bind(crate::clock::today().to_string())
    .scalar(db)
    .await?)
}
