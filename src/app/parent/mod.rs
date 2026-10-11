use renox::prelude::*;

/// Placeholder: replaced by the real feature.
pub struct Parent;

impl Module for Parent {
    fn name(&self) -> &'static str {
        "parent"
    }

    fn routes(&self) -> Routes {
        Routes::new()
            .get("/parent", index)
            .name("parent.index")
            .require_role("parent")
    }
}

async fn index() -> View {
    view(
        "parent/index.html",
        context! { title => "Parent Dashboard" },
    )
}
