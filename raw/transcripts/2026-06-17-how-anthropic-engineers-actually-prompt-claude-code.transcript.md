---
title: "How Anthropic Engineers ACTUALLY Prompt Claude Code"
source_url: "https://www.youtube.com/watch?v=qOvc9IUKEIc"
date_farmed: 2026-06-17
category: transcript
channel: "Austin Marchese"
format: "YouTube video transcript"
---

[0:00] I listened to Anthropic's engineers at
[0:01] the AI Code Summit and I learned
[0:03] something I wasn't expecting. Almost
[0:05] everyone is prompting Claude code wrong.
[0:07] So, I decided to dig deeper and after
[0:08] studying everything Anthropic engineers
[0:10] have published, I uncovered four rules
[0:12] for how they actually prompt Claude
[0:14] code. And it turns out you don't need
[0:15] any technical experience to implement
[0:17] these rules. So, rule number one is they
[0:19] prompt skills, not Claude. Before we get
[0:22] to the rules that will transform how you
[0:23] work, we need to understand the
[0:24] foundation of how they use Claude.
[0:26] Generally, when people first start using
[0:28] AI, they start writing new prompts for
[0:30] everything they do. But, the reality is
[0:31] most of what people do is repetitive
[0:33] tasks. So, Anthropic engineers created
[0:36] Claude skills to help tackle these
[0:38] repetitive tasks. Here's them describing
[0:39] what they are and don't get worried
[0:40] about the technical terms.
[0:42] >> Skills are organized collections of
[0:43] files that package composable procedural
[0:45] knowledge for agents. In other words,
[0:48] they're folders. Barry describes it as
[0:49] procedural knowledge for agents, which
[0:51] is a fancy way to say a way to get a
[0:53] task done. And there's an art to
[0:54] actually creating these skills, which
[0:56] we'll cover in rules two, three, and
[0:57] four. But, first you need to have the
[0:59] mental shift. Stop thinking in
[1:01] traditional prompts, start thinking in
[1:03] prompting Claude skills. This may sound
[1:05] complicated, but it really it's quite
[1:06] simple. Here's what it could look like
[1:08] if you wanted to draft a response to an
[1:09] email. Instead of you having a crazy
[1:11] prompt to help you respond to an email
[1:13] with your voice, your tone, and your
[1:14] writing style, you would just type
[1:15] {slash} draft email and then bring in
[1:17] the email you want to respond to. So,
[1:19] that's how you do it in practice, but
[1:20] conceptually, how should you think about
[1:22] this? I pulled this graph from the
[1:23] Anthropic engineering presentation and
[1:25] added a slight tweak to it. Layer one,
[1:27] you have the AI model. This is the AI
[1:29] that you're using. Layer two is you have
[1:31] the AI agents and the prompts. This is
[1:33] likely how you've been interacting with
[1:34] AI to date, but you want to move up a
[1:36] layer to layer three, which is skills.
[1:38] This is the application layer of the AI
[1:40] world. If you were to compare this to
[1:41] your cell phone, Anthropic is building
[1:43] the phone itself. You have to create the
[1:45] apps. That's the layer to control. And
[1:47] before we get to how to best create
[1:49] these skills, here's a prompt you can
[1:51] run to help you identify the skills that
[1:53] are worth creating. So, you're no longer
[1:54] writing custom prompts, you're writing
[1:56] more specific prompts that clearly
[1:58] reference skills. And this leads to the
[2:00] next topic, which most people get wrong,
[2:01] which is how do you actually build a
[2:03] skill that works? Rule number two is
[2:05] skills are more than prompts. So, you're
[2:07] convinced you need to change how you
[2:08] prompt to prompt skills. So, the next
[2:10] question is how do you actually create
[2:11] skills that work? There's an art to
[2:13] this, a lot like when prompt engineering
[2:14] went viral when ChatGPT first came out,
[2:17] and it's important that you get this
[2:18] right. The act of actually creating the
[2:20] skill is super easy. You can just write
[2:22] in Claude, build me a skill for X, and
[2:23] it'll just create a skill for you. But
[2:25] to use these skills well, you need to
[2:26] understand what's actually inside them.
[2:28] Because it's not just a prompt that
[2:30] lives in a folder. A skill is more than
[2:31] a prompt. Inside a skill, there are
[2:34] three layers. Layer one is the
[2:35] description. This is what Claude checks
[2:38] every time you ask a specific question,
[2:40] and it determines if it should use the
[2:41] skill or not. Think of it like a title
[2:43] on a folder. If the label's vague,
[2:45] Claude's going to have tough time
[2:47] identifying when to use it. If it's
[2:48] specific, it'll know exactly when it
[2:50] needs to use it. And yes, when you're
[2:51] prompting Claude, you don't need to
[2:52] explicitly call a skill if it's properly
[2:55] described. Claude will automatically
[2:56] know when to use it, which is awesome.
[2:58] Layer two is the instructions. Once
[3:00] Claude grabs the skill, this is the
[3:02] playbook it follows. This is a
[3:03] step-by-step process on how to actually
[3:05] complete the task. And layer three are
[3:07] the tools it has access to. This is code
[3:10] scripts, API calls, reference files.
[3:12] This is where a skill becomes a lot more
[3:14] than prompts, and this layer three is
[3:16] where most of the leverage lives, but
[3:18] most people stop at that layer two.
[3:20] Here's Eric from the Anthropic team
[3:21] talking about exactly this. And I think
[3:23] maybe the funniest things I see is that
[3:25] people will put a lot of effort into
[3:27] creating these really beautiful,
[3:29] detailed prompts.
[3:31] Um, and then the tools that they make to
[3:33] give the model are sort of these
[3:34] incredibly bare-bones,
[3:36] uh, like, you know, no documentation,
[3:39] func- like the parameters are named A
[3:41] and B, and it's kind of like, oh, like
[3:43] an engineer wouldn't be able to like,
[3:45] you know, work with this as a,
[3:46] um,
[3:47] you know, work with this as if this was
[3:49] a function they I to use. People obsess
[3:51] over the prompt and skip the tools, the
[3:53] third layer of a skill. Anthropic
[3:55] engineers do the opposite. They focus on
[3:57] these tools. So, instead of this whole
[3:59] back and forth, I created my own custom
[4:00] skill that could check these domains
[4:02] programmatically, so that whatever
[4:04] domains it was telling me, it is already
[4:06] verified that I could go and buy it. So,
[4:08] I gave this skill access to the right
[4:09] tool and it leveled up the entire
[4:11] process. And like I mentioned in rule
[4:13] one, instead of manually thinking about
[4:14] domains, I could have 10 different sub
[4:16] agents using this skill to look through
[4:19] 10,000 plus domains to find the right
[4:21] one. Now, I can do something that I
[4:23] literally would have never been able to
[4:24] do before. Here's a prompt you can use
[4:26] to think deeper about the skills you
[4:27] create, so when you actually go ahead
[4:29] and prompt them, they'll be that much
[4:30] more effective. So, rule number two
[4:32] covers how anthropic engineers make
[4:33] skills, but what skills do they actually
[4:35] create? Rule number three is they build
[4:37] composable skills, not custom skills.
[4:40] Pulling directly from Anthropic's
[4:41] engineering blog about what skills are
[4:43] and how to position them, they are
[4:44] composable, portable, efficient, and
[4:47] powerful. Composability means multiple
[4:49] skills can work together with Claude
[4:51] automatically coordinating which to use.
[4:53] What this means is you should have
[4:54] small, focused, and reusable skills that
[4:57] can work together, versus having a
[4:59] single massive skill that does
[5:00] everything. A concrete example that I
[5:02] experienced when I first started
[5:03] building skills for my content engine, I
[5:05] built a single {slash} content creation
[5:08] skill that did everything. Generated
[5:10] ideas, wrote scripts, drafted social
[5:12] posts, all of it, one skill, a million
[5:15] possibilities, and it just became
[5:16] unmanageable. Every time I wanted to
[5:18] change how scripts were written, I had
[5:20] to rewrite the whole skill and I didn't
[5:21] know what it actually impacted. And so,
[5:23] instead I split it up to more specific
[5:25] skills, right? YouTube idea research,
[5:28] YouTube script writer, LinkedIn post.
[5:30] Each skill had a specific goal in mind.
[5:33] And the benefit is that each can call
[5:35] the other skills, so that they start
[5:37] chaining them together. This may seem a
[5:39] bit overkill, but it really isn't for
[5:41] three specific reasons. The first is
[5:43] that issues are easy to spot. When When
[5:45] focused skill breaks, you know exactly
[5:46] where to look, whereas if it's a giant
[5:49] skill, you don't know what exactly the
[5:51] issue was. The second is that
[5:52] improvements compound. If you update,
[5:55] let's call it YouTube idea research,
[5:57] every workflow that uses the same skill
[5:59] automatically gets upgraded. Whereas if
[6:01] you're using a giant skill, you're going
[6:03] to have overlapping functionality, which
[6:05] means you'll fix it in one skill and it
[6:07] will still be broken in the other. The
[6:09] third is that you can reuse instead of
[6:11] rebuilding. If you build something like
[6:12] the check domain skill I mentioned
[6:14] earlier, you can plug that into any
[6:16] workflow you want. You're not rebuilding
[6:17] the wheel every time with a new
[6:19] workflow. So you know you should break
[6:20] them up, but what's some more technical
[6:22] patterns that you should consider to
[6:24] make these even more powerful. So both
[6:26] of these come from directly how
[6:27] Anthropic engineers actually use them.
[6:29] So pattern one is save scripts inside of
[6:32] skills. This is part of the tools layer
[6:33] of a skill and it's how you actually
[6:35] make them sharper. Here's Barry at the
[6:36] AI Engineering Code Summit talking about
[6:38] how he does exactly this. We kept seeing
[6:40] Claude write the same Python script over
[6:42] and over again to apply styling to
[6:44] slides. So we just asked Claude it
[6:46] inside of the skill as a tool for his
[6:48] version
[6:49] for his future self. Now we can just run
[6:50] the script and that makes everything a
[6:52] lot more consistent, a lot more
[6:53] efficient. Let me break down what he
[6:54] said. Claude kept rewriting the same
[6:56] Python script every session and instead
[6:58] of him letting it rewrite it, they saved
[7:00] the script inside of a skill folder. So
[7:01] now the next session Claude doesn't have
[7:03] to rewrite the script, it just reruns
[7:05] it. And this is so powerful because code
[7:07] is deterministic, which essentially
[7:09] means if you give it the same input, it
[7:11] will give you the same output every
[7:12] single time. Whereas in the AI world,
[7:14] that's not necessarily the case. It
[7:16] interprets it, it guesses, it uses
[7:18] tokens that cost money. And when you
[7:19] have a script inside a skill, you're
[7:21] trading AI tokens for code compute,
[7:24] which is cheaper, faster and repeatable.
[7:26] A general rule of thumb is if you can
[7:28] use code instead of AI, you should. And
[7:30] you don't have to write the code, you
[7:31] can just have AI write it for you once
[7:33] and then you can reuse it as much as you
[7:34] want. The second pattern is you can
[7:36] control who invokes what. Most people
[7:38] don't know this exists, but Anthropic
[7:39] built two flags into Claude's skills
[7:41] that are important to understand. The
[7:43] first is user invocable. If you set this
[7:45] to false, it hides the skill from your
[7:47] slash menu. It means that the user, you
[7:49] or me or whoever, can't directly invoke
[7:51] this skill. It's only a skill for
[7:54] agents. This is perfect for any AI agent
[7:56] specific tools that you don't even want
[7:58] to think about. And then disable model
[8:00] invocation. This does the opposite. Only
[8:02] you can run it and the model can't. This
[8:04] is great for higher risk things like a
[8:06] skill that sends a message or deploys a
[8:08] new version of your code to production.
[8:10] Most of you watching this have likely
[8:11] never heard of either of those things,
[8:13] but now you have it in your bag when
[8:14] you're designing these skills. Here's a
[8:16] prompt you can run to audit your setup
[8:18] to make sure that you're properly
[8:19] applying these things into your skills.
[8:21] Screenshot this and just send the photo
[8:23] into Claude and I highly recommend you
[8:25] do this. So you know how to build skills
[8:27] and what to build, but how do you make
[8:29] these improve over time? And before I
[8:31] get to that, if this is your first video
[8:32] of mine, welcome to channel. But if it's
[8:34] your second or more, here is our
[8:36] anti-slop agreement. The visuals, the
[8:38] testing, the time I put into this video,
[8:40] that's entirely built for humans, not
[8:42] for AI robots or data scrapers. So all I
[8:45] ask is you subscribe as part of this
[8:46] agreement to help this content reach
[8:48] more people so I can keep making videos
[8:50] like this. Rule number four is their
[8:52] prompts get smarter every session.
[8:53] Here's where Anthropic engineers really
[8:55] pull ahead. Their skills and in turn
[8:57] their prompting doesn't just work. They
[8:59] get better every session. When you
[9:01] prompt Claude with a sentence, that
[9:02] prompt disadvantages the moment you
[9:04] close the chat. When you prompt with a
[9:06] skill, the skill stays. And every time
[9:08] you use it, you have a chance to sharpen
[9:10] it. Listen their engineering team talk
[9:12] about exactly this. When you first start
[9:14] using Claude, this standardized format
[9:16] gives a very important guarantee.
[9:18] Anything that Claude writes down can be
[9:20] used efficiently in by the future
[9:21] version of itself. Our goal is that
[9:23] Claude on day 30 of working with you is
[9:25] going to be a lot better on Claude on
[9:27] day one. Every time Claude learns
[9:29] something about how you work, your
[9:30] voice, your process, your edge cases,
[9:32] you write it down in the skill. Next
[9:34] session starts smarter than the last. So
[9:36] how do you actually do this? Every time
[9:37] you run a skill and the output isn't
[9:39] exactly what you want, ask yourself one
[9:42] question. Is this a one-time fix or
[9:44] should this be in the skill forever? If
[9:46] it's forever, update the skill. Add the
[9:48] rule, the example, the edge case. And a
[9:50] lot of people skip this entirely.
[9:51] They're just like, "Okay, run the skill,
[9:53] get an output." Like, continue with
[9:55] their day. But Anthropic engineers use a
[9:57] skill, get the output, then update the
[9:58] skill so that there's a compounding loop
[10:01] that improves over time. And it's really
[10:03] quite simple. Like, it's literally you
[10:05] can just use your chat history as a
[10:07] reference point to improve the skill
[10:09] itself. Just say, "Review the back and
[10:11] forth I just had after using this skill.
[10:14] Can we enhance the skill so this is
[10:16] handled automatically or we don't make
[10:18] the same mistake again?" So, zooming
[10:20] out, these four rules are clear. Use
[10:22] skills, not prompts. Build tools, not
[10:24] just skills with prompts. Build skills
[10:26] that are composable, not custom. And
[10:28] update your skills every time you use
[10:30] them. Using Claude like an engineer
[10:31] doesn't have to be complicated. And if
[10:33] you like this, you'll love this video
[10:35] where I break down how Boris Cherny, the
[10:37] creator of Claude Code, uses Claude
[10:39] skills. It's pretty wild and builds on a
[10:41] lot of what we covered here. I'll see
[10:43] you over there. Peace.
