use huso::app;
use huso::app::content::models::{Flashcard, PlanDay, PlanTask, Question, Subject, Topic};
use renox::prelude::*;
use renox::testing::TestApp;

#[renox::test]
async fn seeding_loads_the_whole_syllabus_and_plan_and_is_repeatable() {
    let test = TestApp::new(app()).await;
    test.kernel().seed().await.unwrap();
    let counts = |test: &TestApp| {
        let db = test.db().clone();
        async move {
            (
                Subject::query().count(&db).await.unwrap(),
                Topic::query().count(&db).await.unwrap(),
                Topic::query()
                    .where_(Topic::PARENT_ID.is_not_null())
                    .count(&db)
                    .await
                    .unwrap(),
                PlanDay::query().count(&db).await.unwrap(),
                PlanTask::query().count(&db).await.unwrap(),
                Flashcard::query().count(&db).await.unwrap(),
                Question::query().count(&db).await.unwrap(),
            )
        }
    };
    let first = counts(&test).await;
    assert_eq!(first.0, 5, "subjects");
    assert_eq!(first.1, 98, "22 topics + 76 subtopics");
    assert_eq!(first.2, 76, "subtopics");
    assert_eq!(first.3, 35, "plan days");
    assert!(first.4 > 100, "plan tasks: {}", first.4);

    test.kernel().seed().await.unwrap();
    assert_eq!(counts(&test).await, first, "a second seed changes nothing");
}

#[renox::test]
async fn the_import_command_can_only_check() {
    let test = TestApp::new(app()).await;
    test.kernel()
        .call("content:import", ["--check"])
        .await
        .unwrap();
}
