//! The two household accounts (student and parent) and their roles.
//!
//! There is no public sign-up: `/register` does not exist (`Auth::without_registration`).
//! `rnx db:seed` creates both accounts from `.env`, and can be run any number of times.

use renox::auth::permissions;
use renox::prelude::*;

pub const STUDENT: &str = "student";
pub const PARENT: &str = "parent";

pub struct Accounts;

impl Module for Accounts {
    fn name(&self) -> &'static str {
        "accounts"
    }

    fn register(&self, app: &mut Registry) {
        app.seeder(|state| async move {
            let db = state.db.clone();
            seed(&db, &state.config).await
        });
    }
}

/// Defines the roles and creates the two users when they do not exist yet.
pub async fn seed(db: &Db, config: &renox::Config) -> Result {
    permissions::define_role(db, STUDENT, &[]).await?;
    permissions::define_role(db, PARENT, &[]).await?;

    let var = |name: &str, default: &str| config.var(name).unwrap_or_else(|| default.to_owned());
    let accounts = [
        (
            "Student",
            var("SEED_STUDENT_EMAIL", "student@huso.local"),
            var("SEED_STUDENT_PASSWORD", "study123"),
            STUDENT,
        ),
        (
            "Parent",
            var("SEED_PARENT_EMAIL", "parent@huso.local"),
            var("SEED_PARENT_PASSWORD", "study123"),
            PARENT,
        ),
    ];
    for (name, email, password, role) in accounts {
        let user = match User::find_by_email(db, &email).await? {
            Some(user) => user,
            None => User::register(db, name, &email, &password).await?,
        };
        user.assign_role(db, role).await?;
    }
    Ok(())
}
