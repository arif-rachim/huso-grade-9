use renox::prelude::*;

/// Placeholder: replaced by the real feature.
pub struct Plan;

impl Module for Plan {
    fn name(&self) -> &'static str {
        "plan"
    }

    fn routes(&self) -> Routes {
        Routes::new()
            .get("/plan", index)
            .name("plan.index")
            .require_auth()
    }
}

async fn index() -> View {
    view("plan/index.html", context! { title => "Plan" })
}
