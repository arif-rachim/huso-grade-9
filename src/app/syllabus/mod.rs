use renox::prelude::*;

/// Placeholder: replaced by the real feature.
pub struct Syllabus;

impl Module for Syllabus {
    fn name(&self) -> &'static str {
        "syllabus"
    }

    fn routes(&self) -> Routes {
        Routes::new()
            .get("/syllabus", index)
            .name("syllabus.index")
            .require_auth()
    }
}

async fn index() -> View {
    view("syllabus/index.html", context! { title => "Syllabus" })
}
