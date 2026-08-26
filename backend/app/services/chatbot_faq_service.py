import re

from app.core.config import settings


FAQ_ENTRIES = (
    {
        "patterns": (
            r"\bhow (?:do|can) i create (?:a )?(?:new )?quiz\b",
            r"\bhow (?:do|can) i make (?:a )?(?:new )?quiz\b",
            r"\bcreate (?:a )?(?:new )?quiz\b",
            r"\bmake (?:a )?(?:new )?quiz\b",
        ),
        "answer": (
            "You can create a quiz from the Create Quiz page. Add the quiz "
            "title and description, choose a category, add up to 3 tags, "
            "choose its visibility, and add your questions and answers "
            "before creating it."
        ),
        "path": "/quizzes/new",
    },
    {
        "patterns": (
            r"\bhow (?:do|can) i import (?:a )?quiz\b",
            r"\bhow (?:do|can) i upload (?:a )?document\b",
            r"\bhow (?:do|can) i create (?:a )?quiz from (?:a )?(?:document|pdf)\b",
            r"\bwhat(?: is| does|'s|’s) on (?:the |my )?import quiz(?: page)?\b",
            r"\bwhat(?: is| does|'s|’s) (?:the |my )?import quiz(?: page)?\b",
            r"\bwhat can i see on (?:the |my )?import quiz(?: page)?\b",
            r"\bwhat can i do on (?:the |my )?import quiz(?: page)?\b",
            r"\bocr\b",
            r"\bimport (?:a )?(?:document|quiz|pdf)\b",
            r"\bupload (?:a )?(?:document|pdf)\b",
        ),
        "answer": (
            "QuizApp can create quizzes from uploaded documents using OCR "
            "and AI. Open the Import Quiz page and upload your document. "
            "QuizApp can extract its content and generate quiz questions "
            "for you to review before creating the quiz."
        ),
        "path": "/import-quiz",
    },
    {
        "patterns": (
            r"\bwhat question types (?:are|do you|does quizapp) support\b",
            r"\bwhat question types are supported\b",
            r"\bwhat (?:are|is) the (?:supported )?question types\b",
            r"\bwhich question types (?:are )?supported\b",
            r"\btypes of questions\b",
        ),
        "answer": (
            "QuizApp currently supports three question types: Multiple "
            "Choice, Written Answer, and Math Work. Multiple Choice lets you "
            "choose from provided options, Written Answer lets you type an "
            "answer, and Math Work provides space to work through a math "
            "problem and enter your final answer."
        ),
        "path": "/quizzes/new",
    },
    {
        "patterns": (
            r"\bwhat (?:is|are) multiple choice\b",
            r"\bhow (?:does|do) multiple choice (?:work|questions work)\b",
            r"\bmultiple choice questions?\b",
        ),
        "answer": (
            "Multiple Choice questions provide a set of answer options. "
            "You select one of the available choices, and QuizApp can grade "
            "the answer automatically after submission."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bwhat (?:is|are) written answer\b",
            r"\bhow (?:does|do) written answer (?:work|questions work)\b",
            r"\bwritten answer questions?\b",
        ),
        "answer": (
            "Written Answer questions let you type your answer instead of "
            "choosing from predefined options. The quiz creator provides "
            "the expected answer when building the quiz."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bwhat (?:is|are) math work\b",
            r"\bhow (?:does|do) math work\b",
            r"\bmath work questions?\b",
            r"\bmath whiteboard\b",
        ),
        "answer": (
            "Math Work questions are designed for solving math problems. "
            "They include a workspace where you can show your work and a "
            "final-answer field. QuizApp uses deterministic math validation "
            "for the final answer."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bwhat(?:'s| is) the difference between public and unlisted\b",
            r"\bpublic (?:or|vs|versus) unlisted\b",
            r"\bwhat does unlisted mean\b",
            r"\bwhat(?:'s| is) unlisted visibility\b",
            r"\bwhat does unlisted visibility mean\b",
            r"\bwhat (?:is|does) public visibility (?:in|on) (?:a )?quiz\b",
            r"\bwhat does public visibility mean\b",
            r"\bwhat(?:'s| is) public visibility\b",
            r"\bwhat does public mean (?:for|on|in) (?:a )?quiz\b",
            r"\bwhat(?:'s| is| does) visibility (?:on|in|for) (?:a )?quiz\b",
            r"\bwhat(?:'s| is) quiz visibility\b",
            r"\bwhat does quiz visibility mean\b",
            r"\bquiz visibility\b",
        ),
        "answer": (
            "A public quiz can appear in QuizApp's discovery experience and "
            "can be found by other users. An unlisted quiz does not appear "
            "in public discovery, but people with its link can still access "
            "it."
        ),
        "path": "/discover",
    },
    {
        "patterns": (
            r"\bwhat (?:is|does) (?:a )?public quiz\b",
            r"\bwhat does public quiz mean\b",
            r"\bcan other users find my public quiz\b",
        ),
        "answer": (
            "Public quizzes can appear in QuizApp's discovery experience "
            "and can be found by other users."
        ),
        "path": "/discover",
    },
    {
        "patterns": (
            r"\bwhat (?:is|does) (?:an )?unlisted quiz\b",
            r"\bwhat does unlisted quiz mean\b",
            r"\bcan people access (?:an|my) unlisted quiz\b",
        ),
        "answer": (
            "An unlisted quiz does not appear in public discovery. It can "
            "still be accessed by someone who has the quiz link."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bhow (?:do|can) i find (?:a )?(?:public )?quiz\b",
            r"\bhow (?:do|can) i discover quizzes\b",
            r"\bwhere (?:do|can) i find quizzes\b",
            r"\bwhat is (?:the )?discover(?: page)?\b",
            r"\bwhat is on (?:the )?discover(?: page)?\b",
            r"\bwhat does (?:the )?discover(?: page)? show\b",
            r"\bwhat can i see on (?:the )?discover(?: page)?\b",
            r"\bwhat can i do on (?:the )?discover(?: page)?\b",
            r"\bdiscover (?:public )?quizzes\b",
            r"\bbrowse quizzes\b",
        ),
        "answer": (
            "You can browse public quizzes through QuizApp's discovery "
            "experience on the Discover page. You can search for quizzes and "
            "filter them by category to find something you want to take."
        ),
        "path": "/discover",
    },
    {
        "patterns": (
            r"\bhow (?:do|can) i search (?:for )?(?:a )?quiz\b",
            r"\bcan i search (?:for )?quizzes\b",
            r"\bsearch quizzes\b",
        ),
        "answer": (
            "Use the search option on the Discover page to find public "
            "quizzes. You can also use category filtering to narrow the "
            "results."
        ),
        "path": "/discover",
    },
    {
        "patterns": (
            r"\bhow (?:do|can) i edit (?:a|my) quiz\b",
            r"\bedit (?:a|my) quiz\b",
            r"\bcan i change (?:a|my) quiz\b",
        ),
        "answer": (
            "Open a quiz you created and choose Edit Quiz. From the editor "
            "you can update its details, visibility, questions, answers, "
            "category, and tags."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bcan i edit someone else(?:'s)? quiz\b",
            r"\bcan i change someone else(?:'s)? quiz\b",
            r"\bwho can edit (?:a )?quiz\b",
        ),
        "answer": (
            "Only the creator of a quiz can edit it. QuizApp enforces quiz "
            "ownership so other users cannot modify quizzes they do not own."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bhow (?:do|can) i take (?:a )?quiz\b",
            r"\bhow (?:do|can) i start (?:a )?quiz\b",
            r"\bstart (?:a )?quiz\b",
        ),
        "answer": (
            "Open the quiz's details page and select Start Quiz. Answer the "
            "questions and submit the quiz when you're finished. QuizApp "
            "will then show the results available for that attempt."
        ),
        "path": "/discover",
    },
    {
        "patterns": (
            r"\bwhere (?:are|can i see) my (?:quiz )?(?:results|attempts)\b",
            r"\bhow (?:do|can) i see my (?:results|attempts)\b",
            r"\bwhat is on (?:my )?attempts(?: page)?\b",
            r"\bwhat is in (?:my )?attempts(?: page)?\b",
            r"\bwhat does (?:the|my) attempts(?: page)? show\b",
            r"\bwhat can i see on (?:my )?attempts(?: page)?\b",
            r"\bwhat can i do on (?:my )?attempts(?: page)?\b",
            r"\battempt history\b",
            r"\bprevious attempts\b",
        ),
        "answer": (
            "Your quiz attempts are available from your attempt history. "
            "You can review previous scores and open individual attempt "
            "results to see how you performed."
        ),
        "path": "/attempts",
    },
    {
        "patterns": (
            r"\bcan i retake (?:a )?quiz\b",
            r"\bcan i take (?:a )?quiz again\b",
            r"\bretake (?:a )?quiz\b",
        ),
        "answer": (
            "Yes. You can retake a quiz, and each submitted attempt is "
            "kept in your attempt history so you can review your performance "
            "across attempts."
        ),
        "path": "/attempts",
    },
    {
        "patterns": (
            r"\bhow (?:is|are) quizzes graded\b",
            r"\bhow does grading work\b",
            r"\bhow (?:is|does) my score (?:work|calculated)\b",
            r"\bquiz grading\b",
        ),
        "answer": (
            "QuizApp grades supported answers using the correct answers "
            "defined for the quiz. Math Work final answers use deterministic "
            "math validation so mathematically equivalent supported answers "
            "can be evaluated consistently."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bwhat are categories and tags\b",
            r"\bwhat (?:are|do) tags\b",
            r"\bquiz tags\b",
            r"\bquiz categories\b",
            r"\bwhat (?:is|does) (?:a )?quiz category\b",
        ),
        "answer": (
            "A category describes the quiz's main subject, while tags add "
            "more specific labels. A quiz can have up to 3 tags. Categories "
            "and tags help organize quizzes and make them easier to "
            "understand and discover."
        ),
        "path": "/discover",
    },
    {
        "patterns": (
            r"\bhow many tags (?:can|may) i (?:add|use)\b",
            r"\bwhat(?:'s| is) the (?:tag|tags) limit\b",
            r"\bmaximum (?:number of )?tags\b",
            r"\bmax (?:number of )?tags\b",
        ),
        "answer": (
            "You can add up to 3 tags to a quiz. Tags are useful for adding "
            "specific labels beyond the quiz's main category."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bhow (?:do|can) i share (?:a|my) quiz\b",
            r"\bcan i share (?:a|my) quiz\b",
            r"\bshare (?:a|my) quiz\b",
            r"\bquiz link\b",
        ),
        "answer": (
            "You can share a quiz by sending its quiz link. Public quizzes "
            "can also be found through Discover, while unlisted quizzes stay "
            "out of public discovery and are accessible through their link."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bhow (?:do|can) i follow (?:a )?user\b",
            r"\bfollow another user\b",
            r"\bhow (?:do|can) i follow someone\b",
        ),
        "answer": (
            "You can follow another QuizApp user from their public profile. "
            "Following makes it easy to keep track of users whose quizzes "
            "interest you."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bwhat (?:are|is) following\b",
            r"\bwhat (?:are|is) followers\b",
            r"\bwhat(?:'s| is) the difference between followers and following\b",
        ),
        "answer": (
            "Followers are users who follow you. Following refers to the "
            "users you have chosen to follow. You can also ask the QuizApp "
            "assistant how many followers you have, who follows you, or who "
            "you follow."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bwhat(?: is| does|'s|’s) (?:the |my )?profile(?: page)?\b",
            r"\bwhat(?: is| does|'s|’s) on (?:the |my )?profile(?: page)?\b",
            r"\bwhat can i see on (?:the |my )?profile(?: page)?\b",
            r"\bwhat can i do on (?:the |my )?profile(?: page)?\b",
            r"\bwhat is on (?:my |the )?profile(?: page)?\b",
            r"\bwhat does (?:my |the )?profile(?: page)? show\b",
            r"\bwhat can i see on (?:my |the )?profile(?: page)?\b",
            r"\bwhat can i do on (?:my |the )?profile(?: page)?\b",
            r"\bwhat (?:is|does) (?:a )?public profile\b",
            r"\bwhat can people see on my profile\b",
            r"\buser profile\b",
        ),
        "answer": (
            "QuizApp profiles let users view public information about "
            "another user, including their public quizzes. Unlisted quizzes "
            "are not included in public profile quiz listings."
        ),
        "path": "/profile",
    },
    {
        "patterns": (
            r"\bwhat(?: is| does|'s|’s) (?:the |my )?dashboard(?: page)?\b",
            r"\bwhat(?: is| does|'s|’s) on (?:the |my )?dashboard(?: page)?\b",
            r"\bwhat can i see on (?:the |my )?dashboard(?: page)?\b",
            r"\bwhat does (?:the |my )?dashboard(?: page)? show\b",
            r"\bwhat can i see in (?:the |my )?dashboard(?: page)?\b",
            r"\bwhat can i do on (?:the |my )?dashboard(?: page)?\b",
            r"\bdashboard stats\b",
        ),
        "answer": (
            "Your dashboard gives you an overview of your QuizApp activity. "
            "It includes statistics such as quizzes created, quizzes taken, "
            "average score, recent quizzes, performance over time, and top "
            "categories."
        ),
        "path": "/dashboard",
    },
    {
        "patterns": (
            r"\bwhat (?:is|does) (?:the )?performance overview\b",
            r"\bwhat does performance overview show\b",
            r"\bperformance over time\b",
        ),
        "answer": (
            "The performance overview helps you see how your quiz scores "
            "change over time. It uses your graded attempt history so you "
            "can understand your performance trend."
        ),
        "path": "/dashboard",
    },
    {
        "patterns": (
            r"\bwhat (?:are|is) (?:my )?top categories\b",
            r"\bwhat does top categories mean\b",
            r"\btop categories\b",
        ),
        "answer": (
            "Top Categories summarizes the categories you have attempted "
            "most often and can show your average performance in those "
            "categories when graded attempt data is available."
        ),
        "path": "/dashboard",
    },
    {
        "patterns": (
            r"\bwhat (?:are|is) ai explanations\b",
            r"\bhow (?:do|does) ai explanations work\b",
            r"\bcan ai explain my (?:answers|results|mistakes)\b",
            r"\bexplain my wrong answers\b",
        ),
        "answer": (
            "QuizApp can provide AI-generated explanations for quiz results "
            "to help you understand answers and learn from mistakes. These "
            "explanations complement your stored quiz results and grading."
        ),
        "path": "/attempts",
    },
    {
        "patterns": (
            r"\bcan i export (?:my )?(?:quiz )?results\b",
            r"\bhow (?:do|can) i export (?:my )?(?:quiz )?results\b",
            r"\bdownload (?:my )?(?:quiz )?results\b",
            r"\bexport (?:my )?(?:quiz )?results\b",
            r"\bresults pdf\b",
        ),
        "answer": (
            "QuizApp supports exporting quiz result information to a PDF so "
            "you can keep or share a formatted copy of your results."
        ),
        "path": "/attempts",
    },
    {
        "patterns": (
            r"\bwhat can (?:you|the chatbot|this chatbot) do\b",
            r"\bwhat can quizapp ai do\b",
            r"\bhow can (?:you|the chatbot) help me\b",
            r"\bchatbot help\b",
            r"\bwhat can i ask (?:you|the chatbot)\b",
        ),
        "answer": (
            "I can help with QuizApp questions and analyze your own activity. "
            "You can ask about quizzes you've taken or created, attempts, "
            "scores, recent quizzes, performance trends, difficult questions, "
            "study recommendations, monthly reports, followers, following, "
            "and how QuizApp features work."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bcan (?:you|the chatbot) see my quiz data\b",
            r"\bcan (?:you|the chatbot) see my attempts\b",
            r"\bcan (?:you|the chatbot) analyze my performance\b",
        ),
        "answer": (
            "I can use the QuizApp data available for your authenticated "
            "account to answer supported questions about your quizzes, "
            "attempts, scores, performance, and other supported activity."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bwhat (?:is|does) (?:the )?monthly report\b",
            r"\bhow (?:does|do) (?:the )?monthly report\b",
            r"\bwhat is my monthly report\b",
        ),
        "answer": (
            "Your monthly report summarizes your QuizApp activity and "
            "performance for a month. It provides useful statistics and "
            "insights based on your quiz activity during that period. You "
            "can ask me for your report for this month or last month."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bwhat (?:are|is) (?:the )?study recommendations\b",
            r"\bhow (?:do|does) study recommendations work\b",
            r"\bcan (?:you|the chatbot) give study recommendations\b",
            r"\bcan (?:you|the chatbot) recommend what to study\b",
        ),
        "answer": (
            "QuizApp's study recommendations use your question performance "
            "to identify questions you've been missing and suggest what you "
            "should focus on next. You can also ask for recommendations "
            "related to a particular quiz."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bcan (?:you|the chatbot) tell if i(?:'m| am) improving\b",
            r"\bhow (?:do|can) i see if i(?:'m| am) improving\b",
            r"\bwhat (?:is|does) performance trend\b",
            r"\bhow does performance trend work\b",
        ),
        "answer": (
            "Yes. I can compare your earlier and more recent graded "
            "performance on a quiz to show whether your score is improving, "
            "declining, or staying about the same."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bcan (?:you|the chatbot) compare my attempts\b",
            r"\bwhat (?:is|does) attempt comparison\b",
            r"\bhow does attempt comparison work\b",
        ),
        "answer": (
            "Yes. I can compare your recent graded attempts so you can see "
            "how your scores changed between attempts. You can also ask for "
            "recent attempts on a specific quiz."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bcan (?:you|the chatbot) identify difficult questions\b",
            r"\bhow (?:do|does) difficult questions work\b",
            r"\bwhat (?:are|is) (?:the )?difficult questions feature\b",
        ),
        "answer": (
            "Yes. I can analyze your question-level performance and identify "
            "questions you've been missing most often, including how many "
            "times you missed them and their miss rate."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bcan (?:you|the chatbot) access my created quizzes\b",
            r"\bcan (?:you|the chatbot) answer questions about quizzes i created\b",
            r"\bwhat can (?:you|the chatbot) tell me about my created quizzes\b",
        ),
        "answer": (
            "Yes. You can ask me to list or count quizzes you've created. "
            "You can also narrow them by visibility, category, title text, "
            "or ask for your newest or oldest created quizzes."
        ),
        "path": None,
    },
    {
        "patterns": (
            r"\bwhat(?: is| does|'s|’s) (?:the |my )?settings(?: page)?\b",
            r"\bwhat(?: is| does|'s|’s) on (?:the |my )?settings(?: page)?\b",
            r"\bwhat can i see on (?:the |my )?settings(?: page)?\b",
            r"\bwhat can i change on (?:the |my )?settings(?: page)?\b",
            r"\bwhat is on (?:my |the )?settings(?: page)?\b",
            r"\bwhat does (?:my |the )?settings(?: page)? show\b",
            r"\bwhat can i see on (?:my |the )?settings(?: page)?\b",
            r"\bwhat can i change on (?:my |the )?settings(?: page)?\b",
            r"\bhow (?:do|can) i change my (?:account )?settings\b",
            r"\bwhere (?:are|is) (?:my )?settings\b",
            r"\baccount settings\b",
        ),
        "answer": (
            "You can manage the account options currently available in "
            "QuizApp from the Settings page."
        ),
        "path": "/settings",
    },

    {
        "patterns": (
            r"\bwhat (?:is|does) (?:the )?audit log(?: page)?\b",
            r"\bwhat is on (?:the )?audit log(?: page)?\b",
            r"\bwhat does (?:the )?audit log(?: page)? show\b",
            r"\bwhat can i see on (?:the )?audit log(?: page)?\b",
            r"\bwhat can i do on (?:the )?audit log(?: page)?\b",
            r"\bwhat is the audit log used for\b",
            r"\bwhat are audit logs\b",
        ),
        "answer": (
            "The Audit Log page shows a record of supported account activity "
            "and actions in QuizApp. It helps you review what actions have "
            "been recorded on your account."
        ),
        "path": "/audit-log",
    },
)


def _build_answer(entry: dict[str, object]) -> str:
    answer = str(entry["answer"])
    path = entry.get("path")

    if not path:
        return answer

    domain = settings.frontend_url.rstrip("/")
    relative_path = str(path)

    if not relative_path.startswith("/"):
        relative_path = f"/{relative_path}"

    return f"{answer}\n\nLink: {domain}{relative_path}"


def answer_chatbot_faq(question: str) -> str | None:
    normalized = " ".join(question.strip().lower().split())

    for entry in FAQ_ENTRIES:
        if any(
            re.search(pattern, normalized)
            for pattern in entry["patterns"]
        ):
            return _build_answer(entry)

    return None
