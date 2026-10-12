//! The content (syllabus, plan, flashcards, questions) as database rows.
//!
//! The JSON files in `content/` are the source of truth. `rnx db:seed` and
//! `rnx content:import` load them into the database; see `files.rs` for the checks.

pub mod files;
pub mod import;
pub mod lesson_file;
pub mod models;

use renox::clap;
use renox::command::AppCommand;
use renox::prelude::*;
use std::path::PathBuf;

pub struct Content;

impl Module for Content {
    fn name(&self) -> &'static str {
        "content"
    }

    fn register(&self, app: &mut Registry) {
        app.model::<models::Subject>();
        app.model::<models::Topic>();
        app.model::<models::PlanDay>();
        app.model::<models::PlanTask>();
        app.model::<models::Flashcard>();
        app.model::<models::Question>();
        app.model::<models::Lesson>();
        app.typed_command::<ImportContent>();
        app.seeder(|state| async move {
            let bundle = files::load_all(&project_dir())
                .map_err(|e| abort(StatusCode::UNPROCESSABLE_ENTITY, e))?;
            import::import(&state.db, &bundle).await?;
            Ok(())
        });
    }
}

/// The directory that holds `content/` and `public/`: where the app runs from.
pub fn project_dir() -> PathBuf {
    std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."))
}

/// Load `content/*.json` into the database (or only check it).
#[derive(clap::Parser)]
#[command(name = "content:import")]
struct ImportContent {
    /// Only validate the files; do not touch the database.
    #[arg(long)]
    check: bool,
}

impl AppCommand for ImportContent {
    async fn run(self, state: AppState) -> Result {
        let bundle = files::load_all(&project_dir())
            .map_err(|e| abort(StatusCode::UNPROCESSABLE_ENTITY, e))?;
        let errors = files::validate(&bundle);
        if !errors.is_empty() {
            println!("{} problem(s) in the content files:", errors.len());
            for e in &errors {
                println!("  - {e}");
            }
            return Err(abort(
                StatusCode::UNPROCESSABLE_ENTITY,
                "The content files are not valid.",
            ));
        }
        if self.check {
            println!("OK");
            return Ok(());
        }
        let r = import::import(&state.db, &bundle).await?;
        println!(
            "Imported {} subjects, {} topics, {} subtopics, {} plan days ({} tasks), {} flashcards, {} questions, {} lessons; archived {}.",
            r.subjects,
            r.topics,
            r.subtopics,
            r.plan_days,
            r.plan_tasks,
            r.flashcards,
            r.questions,
            r.lessons,
            r.archived
        );
        Ok(())
    }
}
