mod app;
pub mod clock;

/// The application: its modules, migrations and seeders. `main.rs` runs it,
/// and tests boot it with `renox::testing::TestApp`.
pub fn app() -> renox::App {
    renox::App::new()
        .embed(renox::embedded!())
        .migrations(renox::migrations!())
        // Login and /account only: the household has two accounts, made by `rnx db:seed`.
        .module(renox::auth::Auth::new().account().without_registration())
        .module(renox::auth::Permissions) // roles: student and parent
        .module(app::accounts::Accounts)
        .module(app::home::Home)
        .module(app::today::Today)
        .module(app::plan::Plan)
        .module(app::flashcards::Flashcards)
        .module(app::practice::Practice)
        .module(app::errors::Errors)
        .module(app::syllabus::Syllabus)
        .module(app::progress::Progress)
        .module(app::parent::Parent)
        // "D-N to HUSO" in the navigation bar of every page.
        .share("huso_countdown", |_ctx| async move {
            Ok(clock::countdown_label(clock::today()))
        })
}
