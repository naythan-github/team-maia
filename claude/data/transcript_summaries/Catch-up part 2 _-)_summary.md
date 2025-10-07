# 📋 Technical Discussion Summary

**File**: Catch-up part 2 _-).vtt
**Processed**: 2025-10-06 21:01:04
**Meeting Type**: Technical
**Duration**: 19874 words (~132 min speaking time)

---

## 🎯 Executive Summary

The conversation between Peter and Naythan Dawe is about using AI to transcribe meeting recordings. Peter mentions that he has been using a tool called Copilot to transcribe the meetings, but Naythan is interested in using his own AI system to compare the transcripts. Peter offers to send Naythan the full transcripts and VTT (WebVTT) files for the previous meeting, but Naythan suggests that he should be able to download the actual transcript rather than the recording. Peter agrees and sends the files to Naythan.

---

## 👥 Participants

- **So therefore it goes to pre**: 1 contributions

---

## 🔍 Problem Statement

The conversation between Naythan Dawe and Peter Mustow is about a meeting that they had regarding the Copilot project. The meeting was held on a video call, and the participants were able to download the VTT (text equivalent format) of the recording for further analysis. The conversation also touches upon the topic of AI and how it can be used to compare the transcripts of different meetings.

---

## 💡 Proposed Solutions

The conversation between Naythan Dawe and Peter Mustow is about a meeting that they had to discuss the Copilot project. The main topic of discussion was the transcripts of their previous meetings, which were in VTT format. Naythan wanted to download the actual transcript rather than the full recording, but Peter explained that the VTT file was just the text equivalent format and that he would send her the files. They also discussed other topics such as the project's progress and the upcoming meeting.

---

## 🏗️ Architecture Decisions

*No information identified for this section*

---

## ⚠️ Technical Risks

*No information identified for this section*

---

## 📋 Implementation Plan

*No information identified for this section*

---

## 🔬 Spike Work & POCs

*No information identified for this section*

---

## 📝 Full Transcript

e690f94e-b4de-4119-bbbf-ec73c6427cac/5-0
<v Naythan Dawe | Orro>Hmm, Yep, yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/9-0
<v Peter Mustow | Orro>And olli,
I'm not actually sure where olli is.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/7-0
<v Naythan Dawe | Orro>Brisbon.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/9-1
<v Peter Mustow | Orro>I don't know if Brisbane. There you go.
So olli, um, is more of a 365 in tune.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/10-0
<v Peter Mustow | Orro>Microsoft 365 guy Um.
And then Alex is he's not so strong in</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/10-1
<v Peter Mustow | Orro>that in that Um area of Intune Um and
device management,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/10-2
<v Peter Mustow | Orro>but he does have the ability to get in
and do things in Microsoft 365.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/10-3
<v Peter Mustow | Orro>So he does do Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/11-0
<v Peter Mustow | Orro>Migrations.
So a lot of the work that I've seen the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/11-1
<v Peter Mustow | Orro>team do so far has been work around
Office 365 migrations where we've got a</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/11-2
<v Peter Mustow | Orro>customer who is selling part of the
business off and Zenitas and Planner is</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/11-3
<v Peter Mustow | Orro>one of those scenarios which is a project
that.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/13-0
<v Peter Mustow | Orro>It's happening at the moment and Alex is,
you know, he's got experience in doing,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/13-1
<v Peter Mustow | Orro>you know,
e-mail migrations and whatnot with tools</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/13-2
<v Peter Mustow | Orro>that we're using.
This tool we're using at the moment is</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/13-3
<v Peter Mustow | Orro>Share Gate.
It's not so great for all the things</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/13-4
<v Peter Mustow | Orro>we're doing,
but it's ticking the boxes for most</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/12-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/13-5
<v Peter Mustow | Orro>things.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/16-0
<v Naythan Dawe | Orro>Yeah,
I looked at Sharegate in the in the past</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/14-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/16-1
<v Naythan Dawe | Orro>and it was like, well,
it's it's kind of OK,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/16-2
<v Naythan Dawe | Orro>but it doesn't really do everything that
I want.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/17-0
<v Peter Mustow | Orro>Yeah,
so we're running into problems with that</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/17-1
<v Peter Mustow | Orro>already. Um,
so like the e-mail migration stuff seems</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/17-2
<v Peter Mustow | Orro>to be working OK, um, to a degree.
But then the actual SharePoint stuff,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/17-3
<v Peter Mustow | Orro>you know,
the customer's got thousands of sites.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/19-0
<v Peter Mustow | Orro>And you know,
they're wanting to consolidate that all</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/19-1
<v Peter Mustow | Orro>in.
They don't have a structure that they</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/19-2
<v Peter Mustow | Orro>wanna move to. And um,
this whole piece of work has been.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/18-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/19-3
<v Peter Mustow | Orro>We had a guy whose name's Corey who's
who's. I don't know if he's left yet,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/19-4
<v Peter Mustow | Orro>but he's finishing up fairly soon.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/20-0
<v Peter Mustow | Orro>Corey came into the into the cloud
business to help from, um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/20-1
<v Peter Mustow | Orro>the network side, I think from memory. Um.
And he's he was helping a guy called</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/20-2
<v Peter Mustow | Orro>Justin, who's no longer with us, um to,
you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/20-3
<v Peter Mustow | Orro>do our statements at works and our
projects and things like that. Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/20-4
<v Peter Mustow | Orro>So a lot of the projects that we're
delivering, um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/21-0
<v Peter Mustow | Orro>Is scoped up. Um. And yeah,
there just wasn't enough devil in the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/21-1
<v Peter Mustow | Orro>detail asked from the customer. And yeah,
here we are today. Um. So yeah, all these,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/21-2
<v Peter Mustow | Orro>all these skill sets. Yeah, Azure.
Um and 365.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/22-0
<v Peter Mustow | Orro>And Alex is the same, um, but they're all,
um, yeah, they're all strong,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/22-1
<v Peter Mustow | Orro>stronger in certain areas than than the
other. So um, yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/22-2
<v Peter Mustow | Orro>they there tends to be with our projects
as well the way we.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/25-0
<v Peter Mustow | Orro>Schedule our engineers to do the projects.
There's a lot of double dipping,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/25-1
<v Peter Mustow | Orro>which I can't stand.
So the guys will be ripped between two or</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/25-2
<v Peter Mustow | Orro>three projects at any given time,
depending on how busy they are.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/23-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/25-3
<v Peter Mustow | Orro>And then there's like dead time.
And then we've got the scenario where we</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/24-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/25-4
<v Peter Mustow | Orro>start a project.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/26-0
<v Peter Mustow | Orro>It goes off the rails because we don't
have the right PMS involved and there's</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/26-1
<v Peter Mustow | Orro>not enough guidance for the customer and
all these questions are raised and it's</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/26-2
<v Peter Mustow | Orro>like pump the brakes and then we have a
project that's stopped.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/26-3
<v Peter Mustow | Orro>So I'd say the delivery of our projects
is very mature.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/27-0
<v Peter Mustow | Orro>We've even got scenarios with NW
Northwestern roads where a year or so ago</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/27-1
<v Peter Mustow | Orro>we sold them an MDM project.
We've built them, we've taken the money,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/27-2
<v Peter Mustow | Orro>but a year and a bit later we still
haven't actually built and delivered the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/27-3
<v Peter Mustow | Orro>MDM project.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/29-0
<v Naythan Dawe | Orro>How does that even happen?
And and and why did they sign off on it?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/28-0
<v Peter Mustow | Orro>Yeah, so we didn't.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/30-0
<v Peter Mustow | Orro>So within, yeah, this is, this is,
this is an internal battle too, right? So.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/29-1
<v Naythan Dawe | Orro>Like what?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/31-0
<v Peter Mustow | Orro>What I've learned and through being
involved so far is we've got our cyber</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/31-1
<v Peter Mustow | Orro>team,
we've got our network team and we have a</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/31-2
<v Peter Mustow | Orro>cyber customer, a network customer.
Then there's discussion with whoever that</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/31-3
<v Peter Mustow | Orro>account manager is or the, you know,
the AM or whatever. Oh,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/31-4
<v Peter Mustow | Orro>you want to do a little bit of cloud or
whatever.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/33-0
<v Peter Mustow | Orro>Oh yeah, cloud could do that.
And then we're we're brought into the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/33-1
<v Peter Mustow | Orro>picture and you know,
we've already been led to the slaughter</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/33-2
<v Peter Mustow | Orro>in terms of what the customer's wanting
and how that side of the business has</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/33-3
<v Peter Mustow | Orro>played the game to get us in there.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/34-0
<v Peter Mustow | Orro>I'll give you,
I'll give you an example of North,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/32-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/34-1
<v Peter Mustow | Orro>Northwestern Roads,
who's one of the biggest thorns in my</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/34-2
<v Peter Mustow | Orro>finger at the moment, right?
So like day two, I joined,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/34-3
<v Peter Mustow | Orro>chucked in this meeting. Long story short,
the network team are doing fine.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/34-4
<v Peter Mustow | Orro>They've got all their 40 Nets and all
their network diagrams and all their</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/34-5
<v Peter Mustow | Orro>processes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/35-0
<v Peter Mustow | Orro>Is in there.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/36-0
<v Peter Mustow | Orro>And then at some point there was, uh,
Cyber Ark sold through the network team</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/36-1
<v Peter Mustow | Orro>and the cyber team to NWR for their OT
environment. Anyway, Long story short,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/36-2
<v Peter Mustow | Orro>they don't have any money.
NWR then they're like, oh,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/36-3
<v Peter Mustow | Orro>this is no good. We don't want to.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/37-0
<v Peter Mustow | Orro>Continue, blah blah blah.
So Aura lost money through that project.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/37-1
<v Peter Mustow | Orro>Then they had to pivot and then they came
up with Azure Bastion as a way of being</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/37-2
<v Peter Mustow | Orro>able to record remote sessions and have a
bastion into certain servers that you</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/37-3
<v Peter Mustow | Orro>could consume OT environment servers,
blah blah blah blah blah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/38-0
<v Peter Mustow | Orro>So then this project got kicked around a
lot and we've kind of just been</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/38-1
<v Peter Mustow | Orro>pigeonholed into this to deliver this
thing that then NWR believes that we're</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/38-2
<v Peter Mustow | Orro>gonna be managing,
moving forward and controlling and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/38-3
<v Peter Mustow | Orro>looking after.
There's no management agreement with it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/40-0
<v Peter Mustow | Orro>Nor will I be writing one for them
because I don't want them as a customer.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/40-1
<v Peter Mustow | Orro>They're a they're a dangerous customer
and it's and it's just because of the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/39-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/40-2
<v Peter Mustow | Orro>stakeholders there.
They've got this contractor guy who's a S</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/40-3
<v Peter Mustow | Orro>who's a security guy who doesn't seem to
understand. You know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/40-4
<v Peter Mustow | Orro>I'm sure he's good at what he does
security wise,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/40-5
<v Peter Mustow | Orro>but why is a security guy leading?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/42-0
<v Peter Mustow | Orro>A modern cloud project or an Azure
project at that, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/42-1
<v Peter Mustow | Orro>and trying to define what that looks like.
There's no road map,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/41-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/42-2
<v Peter Mustow | Orro>there's no strategic framework to
continue with in that space or anything</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/42-3
<v Peter Mustow | Orro>like that, right? So.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/44-0
<v Peter Mustow | Orro>Yeah. From a project perspective,
there's a lot of maturity that we need to</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/44-1
<v Peter Mustow | Orro>inflict into the business and make,
you know, elevate our, our terms.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/44-2
<v Peter Mustow | Orro>You know,
if a customer puts a hold on the project,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/44-3
<v Peter Mustow | Orro>it's a financial cost to the customer,
not us,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/44-4
<v Peter Mustow | Orro>because then we've got an engineer on
bench it delays.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/43-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/46-0
<v Peter Mustow | Orro>The pipeline. You know how it works.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/45-0
<v Naythan Dawe | Orro>Mm-hmm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/47-0
<v Peter Mustow | Orro>So yeah, from a project view,
we need to just,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/47-1
<v Peter Mustow | Orro>we need to stop being sloppy and we need
to think about all the gotchas and have</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/47-2
<v Peter Mustow | Orro>them all there in plain sight.
We need to be doing.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/47-3
<v Peter Mustow | Orro>I'm trying a new thing out with so.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/49-0
<v Peter Mustow | Orro>Um, Goldman, uh,
Goldman Murray Water is a new customer</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/49-1
<v Peter Mustow | Orro>that was introduced by cyber.
I'm trying a new kind of approach of</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/48-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/49-2
<v Peter Mustow | Orro>consulting with them. Um,
so with their they've got Citrix and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/49-3
<v Peter Mustow | Orro>they're thinking about moving to AVD.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/50-0
<v Peter Mustow | Orro>I don't want to do a statement of work
for them.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/50-1
<v Peter Mustow | Orro>So what I've done is I've had a catch up
with their with one of their head guys</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/50-2
<v Peter Mustow | Orro>there, Richard,
and I've just sent him back a six page</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/50-3
<v Peter Mustow | Orro>questionnaire, you know,
on all Citrix questions.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/51-0
<v Peter Mustow | Orro>Their desire and wanting to go to ABD,
I'm just going to get them to populate</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/51-1
<v Peter Mustow | Orro>that and then I'll generate something out
of that which will be rough time frames</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/51-2
<v Peter Mustow | Orro>and estimates and some costings and then
juggle that with him and say is this in</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/51-3
<v Peter Mustow | Orro>the price range of what you're looking at
doing? And if so,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/51-4
<v Peter Mustow | Orro>then let's get something formalized and
then I'll put the effort into actually.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/53-0
<v Peter Mustow | Orro>Building out the design and building out
the scope and then we can go from there.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/52-0
<v Naythan Dawe | Orro>Mm-hmm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/53-1
<v Peter Mustow | Orro>So yeah,
I think that and just from the past as</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/53-2
<v Peter Mustow | Orro>well, right,
with with Versed and even with Telstra</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/53-3
<v Peter Mustow | Orro>Purple when I was helping with tender
responses and even statements at work,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/53-4
<v Peter Mustow | Orro>a lot of the customers would.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/57-0
<v Peter Mustow | Orro>Would go to Versin for, say,
because of the name, because of, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/54-0
<v Naythan Dawe | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/57-1
<v Peter Mustow | Orro>what they were at some point in the
industry.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/57-2
<v Peter Mustow | Orro>We did the great work and we detailed
everything. And then they said, um, no,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/57-3
<v Peter Mustow | Orro>thank you, ma'am.
I'm going somewhere else and they'll take</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/55-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/57-4
<v Peter Mustow | Orro>that artifact, retro it, whatever,
and then they'll go back out to.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/56-0
<v Naythan Dawe | Orro>Yeah, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/59-0
<v Peter Mustow | Orro>Market or they'll give it to their
current provider and say execute these</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/59-1
<v Peter Mustow | Orro>steps.
Here's the baseline of the direction of</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/59-2
<v Peter Mustow | Orro>where you need to go. Um,
do do what you will with it. Um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/59-3
<v Peter Mustow | Orro>but this is what Versin has said and they
know their stuff.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/58-0
<v Naythan Dawe | Orro>Mm mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/60-0
<v Peter Mustow | Orro>So I kinda wanna get us away from that
point as well. Um, so yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/61-0
<v Peter Mustow | Orro>Be keen to chat about ideas around that
from the from a project perspective.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/62-0
<v Naythan Dawe | Orro>Yeah, I.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/63-0
<v Naythan Dawe | Orro>I agree with the. It can just get taken,
but the alternative.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/64-0
<v Naythan Dawe | Orro>Like what you've done for this?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/65-0
<v Naythan Dawe | Orro>Golden Murray Water.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/66-0
<v Naythan Dawe | Orro>Sounds good. It's it's how I have.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/67-0
<v Naythan Dawe | Orro>I've had that as a conversation, like,
you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/67-1
<v Naythan Dawe | Orro>an hour's long chat rather than than that.
Do you think they're going to go through</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/67-2
<v Naythan Dawe | Orro>it?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/68-0
<v Peter Mustow | Orro>I reckon I can. I reckon I can nail it.
I reckon I can get them across the board</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/68-1
<v Peter Mustow | Orro>with it for sure. Now it's.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/69-0
<v Naythan Dawe | Orro>No, I mean,
do you think they're actually going to</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/69-1
<v Naythan Dawe | Orro>like,
are they actually going to go through and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/69-2
<v Naythan Dawe | Orro>answer all those questions?
Or where I'm going with this is you've</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/69-3
<v Naythan Dawe | Orro>done it.
Is it better as a talking script and jump</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/69-4
<v Naythan Dawe | Orro>on a call and ask them and get more
detail and transcribe it as you go</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/69-5
<v Naythan Dawe | Orro>through?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/70-0
<v Peter Mustow | Orro>I think they'll do it. Yeah,
I think they'll do it. Um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/70-1
<v Peter Mustow | Orro>these guys have a pipeline and a like a
execution. Um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/70-2
<v Peter Mustow | Orro>they're obviously working through a piece
of work which is modernizing their cloud,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/70-3
<v Peter Mustow | Orro>right?
So they've talked to us about originally</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/70-4
<v Peter Mustow | Orro>the meeting was about zero trust networks.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/72-0
<v Peter Mustow | Orro>And then it got into AVD.
So our network guys completely dropped</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/72-1
<v Peter Mustow | Orro>the ball with that because they should be
having a conversation around, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/72-2
<v Peter Mustow | Orro>their connectivity and their redundancy
and their networking and their endpoints</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/72-3
<v Peter Mustow | Orro>and all this kind of stuff.
And they they just didn't see that.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/72-4
<v Peter Mustow | Orro>And it's like, guys,
you should be talking about that stuff</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/72-5
<v Peter Mustow | Orro>like, you know, what are?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/73-0
<v Peter Mustow | Orro>What type of networking infrastructure
they wanting to use?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/73-1
<v Peter Mustow | Orro>Are they want to using Microsoft?
Do they want to do this? You know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/73-2
<v Peter Mustow | Orro>zero trust. So they're going to be doing,
are they going to be using Cloudflare?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/73-3
<v Peter Mustow | Orro>Are they going to be using, you know,
well with intro, intro, global access,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/73-4
<v Peter Mustow | Orro>you know that they want to talk to us
about that.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/74-0
<v Peter Mustow | Orro>Um, there's all these different things.
So I find that when we all get in the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/74-1
<v Peter Mustow | Orro>room, we all have.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/76-0
<v Peter Mustow | Orro>We all have our different things that we
wanna do,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/76-1
<v Peter Mustow | Orro>but we don't have an alignment there yet
in the business across all our units to</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/75-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/76-2
<v Peter Mustow | Orro>go in there and show up as one. Um.
And I think of it like, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/76-3
<v Peter Mustow | Orro>in the Telstra days, you know,
the Telstra Tarago,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/76-4
<v Peter Mustow | Orro>everyone would rock up and you know,
you jump in a meeting room and everyone</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/76-5
<v Peter Mustow | Orro>has something to say.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/78-0
<v Peter Mustow | Orro>From all different sides of the business.
And you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/78-1
<v Peter Mustow | Orro>I don't think I was ever in any one of
those meetings where anything eventful</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/78-2
<v Peter Mustow | Orro>came out of those meetings or any
contract that got signed off happened,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/77-0
<v Naythan Dawe | Orro>No. Yeah. Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/78-3
<v Peter Mustow | Orro>right? It was all just words and free.
It was free conversation that the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/78-4
<v Peter Mustow | Orro>customer picked up all this knowledge and
this went off and.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/80-0
<v Peter Mustow | Orro>Ask the question to someone else who
could do it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/79-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/82-0
<v Peter Mustow | Orro>Um, so yeah, I think that, um, yeah,
we'll see with NW um and um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/82-1
<v Peter Mustow | Orro>um MMW water goes, um,
but I think they will probably respond to</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/82-2
<v Peter Mustow | Orro>that.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/81-0
<v Naythan Dawe | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/83-0
<v Peter Mustow | Orro>And give me an update on it, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/86-0
<v Peter Mustow | Orro>It's very similar to the rapid consulting
that, um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/86-1
<v Peter Mustow | Orro>we're doing as a service offering,
so the pricing and the stuff that Hamish</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/86-2
<v Peter Mustow | Orro>sent through. So for housing,
Housing Choice Australia,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/84-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/86-3
<v Peter Mustow | Orro>we're literally gonna be doing workshop
style questionnaire things as well.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/90-0
<v Peter Mustow | Orro>To retain the information and then pump
that through and try and, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/85-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/90-1
<v Peter Mustow | Orro>generate something with AI around it.
How it goes is one thing, but yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/90-2
<v Peter Mustow | Orro>you've got to start somewhere.
If it fails in the first six months,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/87-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/90-3
<v Peter Mustow | Orro>at least we've tried it. Um, but yeah,
we've got to have something there.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/88-0
<v Naythan Dawe | Orro>So.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/91-0
<v Naythan Dawe | Orro>Yeah, when we get to that, I did. Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/93-0
<v Naythan Dawe | Orro>I did quite a lot of research into it,
but then never got to the point of</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/93-1
<v Naythan Dawe | Orro>deploying it.
How I could use Claude to go off,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/93-2
<v Naythan Dawe | Orro>run all the exports,
including what services like I gave it an</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/92-0
<v Peter Mustow | Orro>Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/93-3
<v Naythan Dawe | Orro>example for a customer,
which services would we actually get</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/93-4
<v Naythan Dawe | Orro>meaningful data?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/95-0
<v Naythan Dawe | Orro>From if we dialed up the level of logging.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/94-0
<v Peter Mustow | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/96-0
<v Naythan Dawe | Orro>For a month and gathered it over that
point in time,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/96-1
<v Naythan Dawe | Orro>capture all of the settings before we
dial it up, capture for the month,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/96-2
<v Naythan Dawe | Orro>drop it back down.
How much extra storage are we looking at?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/96-3
<v Naythan Dawe | Orro>You know,
what would the cost of the customer be</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/96-4
<v Naythan Dawe | Orro>$500 in this environment, whatever,
so that there was more for.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/98-0
<v Naythan Dawe | Orro>Deep analysis and then tie that back to
architecture and you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/98-1
<v Naythan Dawe | Orro>pillars and and blah blah blah blah and
it all.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/97-0
<v Peter Mustow | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/98-2
<v Naythan Dawe | Orro>And then you add the human overlay like
to come in and go, yes, that makes sense.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/98-3
<v Naythan Dawe | Orro>No, it doesn't. You know,
you can't just leave it all to the air,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/99-0
<v Peter Mustow | Orro>No, you can't. You need human interaction,
you know? Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/98-4
<v Naythan Dawe | Orro>but yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/100-0
<v Naythan Dawe | Orro>There's, yeah, yeah,
there's there's a ton of stuff,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/100-1
<v Naythan Dawe | Orro>but to filter all of that out, I mean,
etcetera, I just.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/101-0
<v Naythan Dawe | Orro>It was difficult that there was one other
person in the business that was leading</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/101-1
<v Naythan Dawe | Orro>AI more than me, but the.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/102-0
<v Naythan Dawe | Orro>Engineering team was like.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/104-0
<v Naythan Dawe | Orro>And the consultants like enterprise
architect level consultant and stuff</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/103-0
<v Peter Mustow | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/104-1
<v Naythan Dawe | Orro>chatting to him and he's like.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/105-0
<v Naythan Dawe | Orro>How's that going? Oh,
just sitting here trying to work out how</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/105-1
<v Naythan Dawe | Orro>to cleanse this data.
Everything else is like 20 million lines.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/105-2
<v Naythan Dawe | Orro>And I'm like, have you asked, Claude?
Like, no. So I'm like,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/105-3
<v Naythan Dawe | Orro>don't do it yourself.
Get it to analyze it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/108-0
<v Naythan Dawe | Orro>It'll it'll load all these ******* Python
tools and everything else and work it out</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/108-1
<v Naythan Dawe | Orro>for you and tell you what needs to be
done. Don't spend days doing it yourself,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/106-0
<v Peter Mustow | Orro>Exactly.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/108-2
<v Naythan Dawe | Orro>just and then look at the output and then
refine it like.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/107-0
<v Peter Mustow | Orro>Sure.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/110-0
<v Naythan Dawe | Orro>I hadn't thought of that.
And you know what?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/110-1
<v Naythan Dawe | Orro>I bet he didn't actually go and do it.
So anyway, yes,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/109-0
<v Peter Mustow | Orro>No.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/110-2
<v Naythan Dawe | Orro>I saw the rapid stuff and I thought,
this is cool because this is exactly what</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/110-3
<v Naythan Dawe | Orro>I was trying to get better to do so.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/111-0
<v Peter Mustow | Orro>Yep, Yep. So as a as a practice, right.
I think that like your your knowledge and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/111-1
<v Peter Mustow | Orro>your guidance and input, um,
like I'm all that open, open, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/111-2
<v Peter Mustow | Orro>conversation and everything as well,
right. So I'm I'm really hoping to.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/113-0
<v Peter Mustow | Orro>You know, help you,
you help me and we get aligned with</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/112-0
<v Naythan Dawe | Orro>M.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/113-1
<v Peter Mustow | Orro>everything from our projects all the way
down to being able to wrap these with MMR</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/113-2
<v Peter Mustow | Orro>that we can support from our BOU
engineering level that thing.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/116-0
<v Peter Mustow | Orro>Can then get us mini engineering projects
out of those BAU support realms where an</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/114-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/116-1
<v Peter Mustow | Orro>engineer can take a three day piece of
work off the BAU tools and they can</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/115-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/116-2
<v Peter Mustow | Orro>uplift and they can learn,
they can execute and these could be</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/116-3
<v Peter Mustow | Orro>repeatable things that then you know I
and others can create within our business.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/118-0
<v Peter Mustow | Orro>Azure, hybrid and obviously modern work,
that's the goal.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/118-1
<v Peter Mustow | Orro>I'd love to do that because I think that
within that little ecosystem,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/117-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/118-2
<v Peter Mustow | Orro>we retro every three months,
every six months, whatever it is,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/118-3
<v Peter Mustow | Orro>we're uplifting,
we're learning and then we can.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/119-0
<v Peter Mustow | Orro>You know, expand width wise, you know,
instead of taking on more sort of pillars,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/119-1
<v Peter Mustow | Orro>um, as we go. Unless, you know,
Hamish's objective is to get a heap of</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/119-2
<v Peter Mustow | Orro>pillars. I think, like,
let's just be good at what we do 1st and.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/121-0
<v Naythan Dawe | Orro>Yeah, yeah, yeah, yeah.
And and we'll be because the the quicker</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/120-0
<v Peter Mustow | Orro>Grow out of it, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/121-1
<v Naythan Dawe | Orro>we become highly efficient,
the easier it'll be to grow,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/121-2
<v Naythan Dawe | Orro>the happier the customers we've got will
be,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/121-3
<v Naythan Dawe | Orro>the more use cases and examples we'll
have to win the new business.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/122-0
<v Naythan Dawe | Orro>The more referrals, you know,
all the rest of it, that's um uh.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/124-0
<v Naythan Dawe | Orro>I have always said, and I stand by it,
happy customers are sticky customers and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/123-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/124-1
<v Naythan Dawe | Orro>you help them build their Rd.
maps and you build confidence and even if</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/124-2
<v Naythan Dawe | Orro>you first uh.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/127-0
<v Naythan Dawe | Orro>Projects are, um, small. You know,
Cam Robinson from Versant.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/127-1
<v Naythan Dawe | Orro>So as he would put it,
even if the first ones are ***** and bits,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/125-0
<v Peter Mustow | Orro>Yeah, I do. Yeah. Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/127-2
<v Naythan Dawe | Orro>then hopefully you get some of the bigger
stuff on the on the back of it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/126-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/127-3
<v Naythan Dawe | Orro>And that's that's the way I built my
business in Timor,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/127-4
<v Naythan Dawe | Orro>all of our customers originally it was
like.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/130-0
<v Naythan Dawe | Orro>10,000, $20,
000 and we delivered that ahead of time,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/130-1
<v Naythan Dawe | Orro>under budget and everything else.
And they were like, OK, well,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/130-2
<v Naythan Dawe | Orro>let's do the next thing.
And then I helped them create their</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/130-3
<v Naythan Dawe | Orro>three-year Rd.
maps and they'd get close to the end of</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/128-0
<v Peter Mustow | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/130-4
<v Naythan Dawe | Orro>their financial year and they'd go, well,
actually this didn't happen and that</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/130-5
<v Naythan Dawe | Orro>didn't happen and we've got 100K that we
have to spend.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/129-0
<v Peter Mustow | Orro>Yeah, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/132-0
<v Naythan Dawe | Orro>You know that thing we're planning on
doing? Can we do that now? Absolutely.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/131-0
<v Peter Mustow | Orro>Yep, that that that's locker mode, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/132-1
<v Naythan Dawe | Orro>When can you get me the check? Yeah, yeah,
yeah. Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/135-0
<v Peter Mustow | Orro>That's that's awesome.
That's awesome that you do that cause</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/133-0
<v Naythan Dawe | Orro>And because the.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/135-1
<v Peter Mustow | Orro>that's that's where I believe these
repeatable things that eventually I I</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/135-2
<v Peter Mustow | Orro>want to get going.
You know it could be just a stupid little</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/135-3
<v Peter Mustow | Orro>analysis or something that gives a value
to the customer but it's like you know</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/134-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/135-4
<v Peter Mustow | Orro>it's it's $15,
000 to run it and it has an outcome and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/135-5
<v Peter Mustow | Orro>then.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/136-0
<v Peter Mustow | Orro>Everyone is happy because it does a thing
and you're a step ahead, you know?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/138-0
<v Naythan Dawe | Orro>Yep. And and we did it for one customer.
We do a, you know, make it part of.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/137-0
<v Peter Mustow | Orro>Hmm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/138-1
<v Naythan Dawe | Orro>I don't know how this works in this
business, but you know, battle card,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/138-2
<v Naythan Dawe | Orro>data sheet, whatever, sales people, 15K,
you know, assessment, whatever.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/140-0
<v Naythan Dawe | Orro>And then 'cause then we can blue-green
test as well,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/139-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/140-1
<v Naythan Dawe | Orro>like what is the price point that that
product brings in more business?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/142-0
<v Naythan Dawe | Orro>Um, that sort of thing. So</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/141-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/145-0
<v Peter Mustow | Orro>Yes. Um, what else is there? Yeah,
so projects is a bit of a mess, man. Like,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/143-0
<v Naythan Dawe | Orro>Cool.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/145-1
<v Peter Mustow | Orro>it's just it's it's actually where I
spend a lot of my time, to be honest,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/144-0
<v Naythan Dawe | Orro>So.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/145-2
<v Peter Mustow | Orro>because I get dragged into,
I get dragged into all the problems.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/147-0
<v Naythan Dawe | Orro>So that's interesting.
You've got there's only two projects,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/146-0
<v Peter Mustow | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/147-1
<v Naythan Dawe | Orro>people. How many projects are we doing?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/148-0
<v Peter Mustow | Orro>There's only two. Uh, we're doing, um,
there's probably about 4-4 projects on at</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/148-1
<v Peter Mustow | Orro>the moment between the two. We have, uh,
Queensland Parliament Services.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/148-2
<v Peter Mustow | Orro>We're wrapping up the end of this month
with an Intune gig.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/148-3
<v Peter Mustow | Orro>So we did an uplift of Intune policies
and posture for them.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/150-0
<v Naythan Dawe | Orro>That's the one that Mandeep's leading,
right? Is that? No, she's Qantas. Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/149-0
<v Peter Mustow | Orro>Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/151-0
<v Peter Mustow | Orro>No, she's leading the, yeah, yeah.
So she's doing Qantas. Uh,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/151-1
<v Peter Mustow | Orro>that's another one. Sorry. Yeah.
So she's doing Qantas.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/151-2
<v Peter Mustow | Orro>So there's a change that they need done,
Uh,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/151-3
<v Peter Mustow | Orro>which has been taking months and months
for them to schedule. So there's that.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/151-4
<v Peter Mustow | Orro>She's also doing the AMC one.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/152-0
<v Peter Mustow | Orro>Um, which is wrapping up fairly soon.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/153-0
<v Peter Mustow | Orro>Um. And then, yeah,
we've got the Northwestern Roads.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/153-1
<v Peter Mustow | Orro>So we've got the Asia Bastion, which will,
you know that's that's timed, right.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/153-2
<v Peter Mustow | Orro>So even though and this is another thing
in projects too, right,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/153-3
<v Peter Mustow | Orro>when we if we estimate a project to be.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/155-0
<v Peter Mustow | Orro>Six week engagement and we in our
statement of work say look we've we've</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/155-1
<v Peter Mustow | Orro>come to an agreement that it's it's six
weeks of paid work but the duration of</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/155-2
<v Peter Mustow | Orro>the project is 12 weeks.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/159-0
<v Peter Mustow | Orro>Uh, we should be,
we should be at least putting in the,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/154-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/159-1
<v Peter Mustow | Orro>you know,
penciling in those timeframes on when our</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/159-2
<v Peter Mustow | Orro>engineers should be available for those,
if that's part of a broader project.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/156-0
<v Naythan Dawe | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/159-3
<v Peter Mustow | Orro>But we're not doing that, right?
So we're not even.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/157-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/162-0
<v Naythan Dawe | Orro>And that's part of the way we quote.
That's where we're building out the quote.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/160-0
<v Peter Mustow | Orro>Correct.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/162-1
<v Naythan Dawe | Orro>So that leads nicely into how we're
building out the quotes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/162-2
<v Naythan Dawe | Orro>Where's our quoting tool?
Like almost everywhere I've worked,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/162-3
<v Naythan Dawe | Orro>including the business that I built,
had an Excel based quoting tool.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/161-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/162-4
<v Naythan Dawe | Orro>All of them had a CPQ plan for a project
from SAS.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/163-0
<v Naythan Dawe | Orro>Product. None of them ever made it.
So how are we doing that?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/164-0
<v Peter Mustow | Orro>Yeah, sorry.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/165-0
<v Naythan Dawe | Orro>And is it repeatable and are we learning
from it?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/168-0
<v Peter Mustow | Orro>Yes, good questions.
I we have our potential which is raised</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/168-1
<v Peter Mustow | Orro>in OTC. Actually,
did you want me to run through that</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/167-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/168-2
<v Peter Mustow | Orro>quickly with you? Well, Yep.
So what I'll do or quickly.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/169-0
<v Naythan Dawe | Orro>My brain's already exploding with
information.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/170-0
<v Peter Mustow | Orro>Yeah, I just, I just,
I'm just a fan of overload. And then,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/169-1
<v Naythan Dawe | Orro>Doesn't matter if we squeeze a bit more
in.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/170-1
<v Peter Mustow | Orro>yeah,
you'll ask questions about things and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/170-2
<v Peter Mustow | Orro>that'll be the stuff that you just missed
out on. That's fine. Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/170-3
<v Peter Mustow | Orro>So I got introduced to this not long ago.
Um, but as you can see here, like these,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/170-4
<v Peter Mustow | Orro>this is our cloud board, excuse the size,
but um, this.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/172-0
<v Peter Mustow | Orro>This is what we talk about every day,
right?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/172-1
<v Peter Mustow | Orro>So these are all the account managers and
SDM's and our logger potential.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/172-2
<v Peter Mustow | Orro>And then technically we these should all
be child tickets,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/172-3
<v Peter Mustow | Orro>but we get assigned the parent, whatever.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/171-0
<v Naythan Dawe | Orro>So is this in OTC? Is it?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/175-0
<v Peter Mustow | Orro>This is OTC. Yeah. So this,
this is a custom dashboard that Gina</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/173-0
<v Naythan Dawe | Orro>Yeah, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/175-1
<v Peter Mustow | Orro>built for us to make it more pleasant for
us to do, right? But essentially, um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/174-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/175-2
<v Peter Mustow | Orro>you know, like Alpesh,
he logged this ticket, right?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/175-3
<v Peter Mustow | Orro>And it gets assigned. Uh,
it should be a parent ticket.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/177-0
<v Peter Mustow | Orro>Should be a parent ticket from him and
then he should create a child ticket in</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/177-1
<v Peter Mustow | Orro>there and assign the child ticket to
cloud. Yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/176-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/177-2
<v Peter Mustow | Orro>but because it's just a it's just
something for cloud.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/177-3
<v Peter Mustow | Orro>He just assigns it to cloud as a parent.
So it doesn't necessarily really matter</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/177-4
<v Peter Mustow | Orro>if he had a if he had a.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/179-0
<v Peter Mustow | Orro>Deal where you're doing something with
say cyber wanted the customer wanted</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/179-1
<v Peter Mustow | Orro>Sentinel one and then we were doing the
Intune part.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/179-2
<v Peter Mustow | Orro>The Sentinel one part would go to cyber
to quote and they would do have a child</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/179-3
<v Peter Mustow | Orro>ticket for raising their quote and their
pricing and then they submit that,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/179-4
<v Peter Mustow | Orro>close it off and it goes to the parent
and then.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/181-0
<v Peter Mustow | Orro>Cloud would then do you know Intune
configuration, project plan,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/181-1
<v Peter Mustow | Orro>all that kind of stuff, statement of work,
blah blah blah and we would close our</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/181-2
<v Peter Mustow | Orro>child ticket off and then in the parent
would have all the quotes there and then</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/181-3
<v Peter Mustow | Orro>the the Alpesh would then need to
consolidate all that and then send that</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/181-4
<v Peter Mustow | Orro>to the customer and walk them through it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/182-0
<v Peter Mustow | Orro>That's kind of how it works.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/180-0
<v Naythan Dawe | Orro>OK.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/183-0
<v Peter Mustow | Orro>Then obviously it raises a sales order
that gets PDF D and sent to the customer</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/183-1
<v Peter Mustow | Orro>through for a sign or whatever it is.
It's just an OTC sign off page.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/183-2
<v Peter Mustow | Orro>Customer signs it and then it goes to
Richard's team who's who's the PMO and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/183-3
<v Peter Mustow | Orro>then he start,
he puts it in there as a project.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/184-0
<v Peter Mustow | Orro>Gets all the time frames logged up,
locks in all our resourcing,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/184-1
<v Peter Mustow | Orro>project managers,
project engineers and then negotiates.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/184-2
<v Peter Mustow | Orro>Well, you know, um kicks off that that,
um that session with the customer and the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/184-3
<v Peter Mustow | Orro>project starts to go now.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/185-0
<v Peter Mustow | Orro>What I do is when I get time to do the
quotes and things,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/185-1
<v Peter Mustow | Orro>the pre sales is this one as an example.
If I wanted to quote this with uh,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/185-2
<v Peter Mustow | Orro>so I do my statement of work in my doc
and then I'll PDF it and I'll attach it</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/185-3
<v Peter Mustow | Orro>to this um to this particular um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/186-0
<v Peter Mustow | Orro>Ticket.
Then I go to the quote tool and I select</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/186-1
<v Peter Mustow | Orro>quote and I'll select the customer.
So let's just go bound.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/188-0
<v Peter Mustow | Orro>So bound,
we find them in the list and then under</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/188-1
<v Peter Mustow | Orro>potentials they all show.
So we can see here that that's the only</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/188-2
<v Peter Mustow | Orro>potential that's underneath that customer.
Other customers have a boatload of other</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/187-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/188-3
<v Peter Mustow | Orro>things.
So it's just whatever the business is</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/188-4
<v Peter Mustow | Orro>working on.
I hit submit and then I can just double</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/188-5
<v Peter Mustow | Orro>check that you know Chris is the A is the.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/189-0
<v Peter Mustow | Orro>Account manager. Yep,
I can see all the information there.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/189-1
<v Peter Mustow | Orro>It's gonna be a quote by me.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/190-0
<v Peter Mustow | Orro>Um, internal notes if needed,
but the quote period is valid for one</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/190-1
<v Peter Mustow | Orro>month.
I'll hit next and this is where I can</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/190-2
<v Peter Mustow | Orro>start to build out my my quote.
So I can type in here,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/190-3
<v Peter Mustow | Orro>you know I can have a cloud engineer.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/192-0
<v Peter Mustow | Orro>They're 1748 and I might need, you know,
five days of effort and it quotes me at</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/192-1
<v Peter Mustow | Orro>that and after that I hit next and it
will go ahead. It'll generate the letter,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/191-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/192-2
<v Peter Mustow | Orro>uh,
it'll generate the quote and attach it to</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/192-3
<v Peter Mustow | Orro>the potential.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/193-0
<v Peter Mustow | Orro>And then I can close that ticket off and
it and it just gets added as an</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/193-1
<v Peter Mustow | Orro>attachment quote.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/194-0
<v Peter Mustow | Orro>Um,
one thing to note is the quoting tool</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/194-1
<v Peter Mustow | Orro>will take care of if the customer is an
Oro customer or an NW customer.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/194-2
<v Peter Mustow | Orro>At the moment N um Oro is um working
through NW customers and uplifting them</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/194-3
<v Peter Mustow | Orro>onto Oro terms and conditions and all
that kind of business stuff, right?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/194-4
<v Peter Mustow | Orro>So if the.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/195-0
<v Peter Mustow | Orro>Customer is still an NW customer and they
haven't been moved,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/195-1
<v Peter Mustow | Orro>then the quote tool will have the NW logo
on the quote Uh versus the Oro logo.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/195-2
<v Peter Mustow | Orro>So that's all automated.
We don't have to worry about that.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/195-3
<v Peter Mustow | Orro>Eventually we won't need to worry cause
it'll all just be Oro, but um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/199-0
<v Peter Mustow | Orro>Yeah, essentially this is,
this is the quoting tool.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/199-1
<v Peter Mustow | Orro>This comes up as a standard cause it's
mainly built for the network team,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/196-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/199-2
<v Peter Mustow | Orro>this tool. But yeah, we can, we can just,
yeah, we could use it occasionally.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/197-0
<v Naythan Dawe | Orro>And we may use it occasionally, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/199-3
<v Peter Mustow | Orro>We can just zero it out and it will just
it disappeared.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/198-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/200-0
<v Peter Mustow | Orro>Um, essentially, right?
The stuff that Hamish is working through</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/200-1
<v Peter Mustow | Orro>with the CIS and the line items and the
service offerings, right?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/200-2
<v Peter Mustow | Orro>Eventually we'll be able to go in here
and just go, you know, um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/200-3
<v Peter Mustow | Orro>enter assessment.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/203-0
<v Peter Mustow | Orro>And we just find what that service
offering is and we can just add that and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/203-1
<v Peter Mustow | Orro>just you know it is a set cost and then
we just sit add and and submit and next,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/201-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/203-2
<v Peter Mustow | Orro>next,
next um or the customer can consume that</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/202-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/203-3
<v Peter Mustow | Orro>from their self-service portal in OTC
when that time does come.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/204-0
<v Naythan Dawe | Orro>So.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/205-0
<v Naythan Dawe | Orro>How are you actually building out?
How are you pricing up a statement of</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/205-1
<v Naythan Dawe | Orro>work?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/206-0
<v Peter Mustow | Orro>Yeah,
So what I will do is in a statement of</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/206-1
<v Peter Mustow | Orro>work, I'll go through and whatever the,
um, the work is that needs to be done, uh,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/206-2
<v Peter Mustow | Orro>I'll have some form of knowledge of,
you know, how to how to do that thing,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/206-3
<v Peter Mustow | Orro>right? Let's just take an easy one that.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/207-0
<v Peter Mustow | Orro>We get a lot right.
Customer will come to us and I'll say, oh,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/207-1
<v Peter Mustow | Orro>we need you to to decommission the server,
you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/207-2
<v Peter Mustow | Orro>and it's like this is not necessarily
project work for me and this is where I'm</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/207-3
<v Peter Mustow | Orro>wanting to get a lot of this stuff that
comes from the SDM's and the customers.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/209-0
<v Peter Mustow | Orro>To go more towards the BAU engineering
because it's like it's it's no more than</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/208-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/210-0
<v Naythan Dawe | Orro>No, it's it's it's not in the contract,
but it is effectively BAU.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/209-1
<v Peter Mustow | Orro>a day's work. So I.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/211-0
<v Peter Mustow | Orro>Correct. Yeah.
So what's happening is the STMS go, well,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/211-1
<v Peter Mustow | Orro>the BAU don't do project work.
So therefore it goes to pre-sales and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/211-2
<v Peter Mustow | Orro>then it gets a project engineer assigned
to it where we've, um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/211-3
<v Peter Mustow | Orro>I guess yet to be confirmed,
but the way I see it is if it's.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/212-0
<v Peter Mustow | Orro>If it's of three days of work as an
example in estimate or or or billing,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/212-1
<v Peter Mustow | Orro>then we should be looking at a a BAU
engineer that has that skill set to then</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/212-2
<v Peter Mustow | Orro>perform that three day work as an example.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/213-0
<v Naythan Dawe | Orro>Yeah, yeah.
As long as as long as there's a</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/213-1
<v Naythan Dawe | Orro>complexity gate in there, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/214-0
<v Peter Mustow | Orro>Correct.
I would say that like if we're looking at</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/214-1
<v Peter Mustow | Orro>Level 3 entry resolver,
which is where we need to be and what</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/214-2
<v Peter Mustow | Orro>Hamish is trying to do by getting one and
two level into Oro support internal</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/214-3
<v Peter Mustow | Orro>moving that function across and we just
are Level 3.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/216-0
<v Peter Mustow | Orro>Whatever you want to call it,
then our skill sets of engineers should</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/216-1
<v Peter Mustow | Orro>be able to go ahead and decommission a
server as an example, right?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/215-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/218-0
<v Naythan Dawe | Orro>Oh yeah, in that example, yes,
I was just thinking about the three day</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/218-1
<v Naythan Dawe | Orro>because it's, you know,
sometimes you could be turning something</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/218-2
<v Naythan Dawe | Orro>if you're decommissioning, yes,
if you're turning something on and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/217-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/218-3
<v Naythan Dawe | Orro>there's always the what else is
interlinked.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/219-0
<v Naythan Dawe | Orro>You know, so as long as there's a.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/220-0
<v Naythan Dawe | Orro>Once we have confidence in those that are
doing it to know that they need to reach</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/220-1
<v Naythan Dawe | Orro>out and whatever and blah blah blah,
but that is a problem for another day.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/221-0
<v Peter Mustow | Orro>Yeah, so to give you an example of, um,
one I did recently, right? So sister.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/222-0
<v Peter Mustow | Orro>Sisters of Good Samaritan.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/223-0
<v Peter Mustow | Orro>Statement of work server decommissioning.
It's only because like it just came to my</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/223-1
<v Peter Mustow | Orro>head when I was talking to you.
But this is what a standard statement of</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/223-2
<v Peter Mustow | Orro>work looks like. I'd love to improve it,
but yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/223-3
<v Peter Mustow | Orro>I'm trying to get more of a baseline so
that we can actually just update the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/223-4
<v Peter Mustow | Orro>filters and the names change so we have
to go in and hard type these.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/224-0
<v Peter Mustow | Orro>If we just update them in the properties,
um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/225-0
<v Naythan Dawe | Orro>Have you seen, um,
the RFP tool that Jono wrote?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/227-0
<v Peter Mustow | Orro>I'm not yet, no.
I've I was connecting with Jono a couple</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/227-1
<v Peter Mustow | Orro>of months back,
but my my world's just been crazy with</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/227-2
<v Peter Mustow | Orro>escalations and whatnot,
and I've just been helping Hamish not get</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/226-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/227-3
<v Peter Mustow | Orro>all that as well,
because what would happen was he was</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/227-4
<v Peter Mustow | Orro>getting absolutely.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/228-0
<v Peter Mustow | Orro>Slammed with every single thing and also
didn't necessarily have that background</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/228-1
<v Peter Mustow | Orro>on the thing or wouldn't know where to
start. And that's fine.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/228-2
<v Peter Mustow | Orro>So this is where I've come in and I've
just picked all the **** up and I'm just</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/228-3
<v Peter Mustow | Orro>trying to get through it all to sort of,
you know, shoot him, I guess, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/231-0
<v Naythan Dawe | Orro>Yeah.
The only reason I'm mentioning that is</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/229-0
<v Peter Mustow | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/231-1
<v Naythan Dawe | Orro>because if my memory says from what I saw,
it's a sort of thing that I think we</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/231-2
<v Naythan Dawe | Orro>could piggyback off relatively easily and
provide, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/230-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/231-3
<v Naythan Dawe | Orro>markdown and the rest of all this stuff
is generated nicely because in my</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/231-4
<v Naythan Dawe | Orro>experience, anytime.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/233-0
<v Naythan Dawe | Orro>That anybody edit a Word document,
it ends up looking like **** in no time.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/232-0
<v Peter Mustow | Orro>Yes, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/233-1
<v Naythan Dawe | Orro>It just just does not lend itself to
multiple edits without causing problems.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/235-0
<v Peter Mustow | Orro>Yeah,
and my O my OCD in this stuff is crazy.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/235-1
<v Peter Mustow | Orro>Like if I'll have a full stop on this
line or, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/235-2
<v Peter Mustow | Orro>someone goes in and changes things.
So yeah, I I I agree.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/234-0
<v Naythan Dawe | Orro>Hmm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/236-0
<v Naythan Dawe | Orro>So um, just as an aside in my cloud.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/239-0
<v Naythan Dawe | Orro>Environment on the cloud agent.
I now rather than work with the markdown</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/239-1
<v Naythan Dawe | Orro>and my idea in the future for us if we're
using confluence is if it generates</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/239-2
<v Naythan Dawe | Orro>something in markdown that's huge for me,
I just get it to export it right straight</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/237-0
<v Peter Mustow | Orro>E.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/239-3
<v Naythan Dawe | Orro>to the space in in confluence and I read
it there and I was like you know we could</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/238-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/239-4
<v Naythan Dawe | Orro>build out quite good.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/241-0
<v Naythan Dawe | Orro>Documents and stuff in Confluence and
possibly pull them back through a filter</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/241-1
<v Naythan Dawe | Orro>like that because Confluence doesn't go
to Word neatly,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/240-0
<v Peter Mustow | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/241-2
<v Naythan Dawe | Orro>but it'll pull that back and turn it into
Markdown,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/241-3
<v Naythan Dawe | Orro>which then will come out the word quite
neatly.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/244-0
<v Naythan Dawe | Orro>Ideas on the on the fly like you know,
because not everybody,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/242-0
<v Peter Mustow | Orro>EE.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/243-0
<v Peter Mustow | Orro>It's a good idea, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/244-1
<v Naythan Dawe | Orro>not everybody can read Markdown easily.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/245-0
<v Peter Mustow | Orro>No, no. Yeah, it's, um,
that's a good idea. Maybe we can. Yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/245-1
<v Peter Mustow | Orro>I think that the I've heard pretty cool
things about the tool that he's been</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/245-2
<v Peter Mustow | Orro>building. Um. But yeah, I'll,
I'll just touch base with him when I get</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/245-3
<v Peter Mustow | Orro>back, when I get time. But um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/246-0
<v Naythan Dawe | Orro>Yeah, yeah.
He's slammed at the moment anyway,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/247-0
<v Peter Mustow | Orro>Yeah, but oh, it's just unreal. Everyone.
Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/247-1
<v Peter Mustow | Orro>And it's the people that are under demand
to the the ones that are the busiest.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/246-1
<v Naythan Dawe | Orro>but yeah, everyone is.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/247-2
<v Peter Mustow | Orro>And this is,
this is what really kind of I've I've</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/247-3
<v Peter Mustow | Orro>observed as well.
And it's like there's so many people in</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/247-4
<v Peter Mustow | Orro>our cloud team.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/248-0
<v Peter Mustow | Orro>And they're not. They say they're busy,
but they're not busy.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/249-0
<v Naythan Dawe | Orro>They won't, no dizzle.
I was talking to MV today and I said.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/255-0
<v Naythan Dawe | Orro>I'm just going to say it.
This sounds like a room full of headless</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/250-0
<v Peter Mustow | Orro>And.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/252-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/255-1
<v Naythan Dawe | Orro>chickens.
Like there's just so much running around</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/253-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/255-2
<v Naythan Dawe | Orro>and panicking. And it's like, just,
do you know what I just realized why</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/254-0
<v Peter Mustow | Orro>No, it's not ownership.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/255-3
<v Naythan Dawe | Orro>Hamish? No,
I was just realized why Hamish.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/258-0
<v Naythan Dawe | Orro>Jumped when I contacted him about this
role because he has seen me in a meeting</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/258-1
<v Naythan Dawe | Orro>with 30 execs when that meltdown happened
and just calm head in the room.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/258-2
<v Naythan Dawe | Orro>This is all we need to do one thing next
at a time.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/256-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/258-3
<v Naythan Dawe | Orro>I only just realized that this is similar.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/261-0
<v Peter Mustow | Orro>Yes, it is. It is. And when, when,
when he mentioned you when,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/259-0
<v Naythan Dawe | Orro>So um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/261-1
<v Peter Mustow | Orro>when your name came up,
cause we haven't crossed paths at Purple</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/261-2
<v Peter Mustow | Orro>or Telstra before either, right. So um,
and that's OK. But um, yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/260-0
<v Naythan Dawe | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/261-3
<v Peter Mustow | Orro>he did mention you and he mentioned cause
I was aware of the I didn't join that</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/261-4
<v Peter Mustow | Orro>call by the way.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/263-0
<v Peter Mustow | Orro>The the triage call with the issue that
they had with the, is it CXC?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/263-1
<v Peter Mustow | Orro>What was the system again? CSX. Yeah,
I didn't join because yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/262-0
<v Naythan Dawe | Orro>CSX.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/263-2
<v Peter Mustow | Orro>previously I've been involved in other
things with that platform.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/264-0
<v Peter Mustow | Orro>At a given time. And I was just like, no,
I'm busy. Um, so yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/264-1
<v Peter Mustow | Orro>otherwise I would have probably seen you
on the call. But um, yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/264-2
<v Peter Mustow | Orro>he did mention that you were, you know,
in in charge of that. And I said, look,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/264-3
<v Peter Mustow | Orro>you know, if you can, if you,
if you know how to handle stakeholders</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/264-4
<v Peter Mustow | Orro>and you can get a, a, an outcome.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/265-0
<v Peter Mustow | Orro>To a situation which is, you know,
pretty ****, right?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/265-1
<v Peter Mustow | Orro>And there's there's not many winners in
it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/265-2
<v Peter Mustow | Orro>But if you can get out the other end and
have, you know, a, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/265-3
<v Peter Mustow | Orro>a fairly good outcome,
then that's someone we need on our team,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/265-4
<v Peter Mustow | Orro>right?
Because we definitely need to be able to,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/265-5
<v Peter Mustow | Orro>you know,
handle that internally as well as our</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/265-6
<v Peter Mustow | Orro>customers because it's just, it's crazy.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/269-0
<v Peter Mustow | Orro>It it. And to give you an idea,
like I haven't done anything that I've</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/269-1
<v Peter Mustow | Orro>been brought on board to do, you know,
for the business because I've I've. Yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/266-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/267-0
<v Naythan Dawe | Orro>And it doesn't surprise me, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/269-2
<v Peter Mustow | Orro>yeah. So yeah, look, this is, this is,
this is something that, yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/269-3
<v Peter Mustow | Orro>absolutely we can mature,
but at the moment it's very manual.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/269-4
<v Peter Mustow | Orro>So I'm going through, um, cap.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/268-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/271-0
<v Peter Mustow | Orro>And capturing the, you know, you know,
they said, oh,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/271-1
<v Peter Mustow | Orro>what what apps are on our server?
What should we need to be concerned about?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/271-2
<v Peter Mustow | Orro>You know,
they're wanting to remove File Maker Pro,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/271-3
<v Peter Mustow | Orro>right?
But then they've got this accounting</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/271-4
<v Peter Mustow | Orro>software and this asset software and a
SQL Server that's probably connected to</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/271-5
<v Peter Mustow | Orro>it, which they haven't thought about.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/270-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/272-0
<v Peter Mustow | Orro>You know,
so I go back and give them this and give</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/272-1
<v Peter Mustow | Orro>them the deduction, you know, and this is,
this is sort of what, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/272-2
<v Peter Mustow | Orro>at a higher level, you know,
the statement of what it looks like.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/272-3
<v Peter Mustow | Orro>But stuff like this, three hours of work,
very easy, clear, you know, directions.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/272-4
<v Peter Mustow | Orro>Obviously behind the scenes we're doing a
lot more than this and this is where we</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/272-5
<v Peter Mustow | Orro>need to uplift our maturity.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/273-0
<v Peter Mustow | Orro>But yeah,
I did one similar to this for the Ampac</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/273-1
<v Peter Mustow | Orro>and Llewellyn,
as I was talking about earlier,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/273-2
<v Peter Mustow | Orro>missed a few steps and it's probably cost
us that customer. So yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/273-3
<v Peter Mustow | Orro>it's it's disappointing because there was
lots of work there that we could have</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/273-4
<v Peter Mustow | Orro>probably got through them, but.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/274-0
<v Peter Mustow | Orro>Yeah, at the moment,
that's how we're doing our statements at</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/274-1
<v Peter Mustow | Orro>work. So yeah, the quote, um,
if I just go back to that,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/274-2
<v Peter Mustow | Orro>the quotes look like that.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/276-0
<v Naythan Dawe | Orro>Are we quoting on anything more complex
like, you know, Intune deployments?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/275-0
<v Peter Mustow | Orro>Just gives the.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/278-0
<v Peter Mustow | Orro>Yeah. So we are, Yeah.
So that's that's the stuff that, um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/277-0
<v Naythan Dawe | Orro>Windows 11 rollouts like.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/278-1
<v Peter Mustow | Orro>Hamish has been working on with this. Um,
so he's been picking up these ones</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/278-2
<v Peter Mustow | Orro>because he's been working with Jono
around this,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/278-3
<v Peter Mustow | Orro>so he wanted to work with Jono on it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/279-0
<v Peter Mustow | Orro>But essentially, yeah,
this is this is a statement of work</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/279-1
<v Peter Mustow | Orro>around that.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/280-0
<v Peter Mustow | Orro>Yeah.
So it goes through obviously the the,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/280-1
<v Peter Mustow | Orro>the different things that we're doing.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/281-0
<v Peter Mustow | Orro>Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/282-0
<v Peter Mustow | Orro>Yeah. Other other projects we've got,
we've got sort of, um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/282-1
<v Peter Mustow | Orro>like detailed designs to a degree where
we're following sort of like a standard,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/282-2
<v Peter Mustow | Orro>but in terms of.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/284-0
<v Peter Mustow | Orro>Yeah, in terms of like,
I haven't seen anything that's like,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/284-1
<v Peter Mustow | Orro>you know, like a Telstra or purple.
You'd have like a full sad that you do</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/284-2
<v Peter Mustow | Orro>before you even start work.
I haven't seen anything like that.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/283-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/285-0
<v Peter Mustow | Orro>Um, yeah.
And I don't know if that's the direction</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/285-1
<v Peter Mustow | Orro>that we wanna take essentially for things.
Um, I really don't know.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/285-2
<v Peter Mustow | Orro>Things are things that I'm looking at to
give you an idea. So behind the scenes,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/285-3
<v Peter Mustow | Orro>uh, when I get time, I've been working on.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/287-0
<v Peter Mustow | Orro>Like service offerings for Azure, right?
So this is just me just sand pitting an</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/287-1
<v Peter Mustow | Orro>idea, um, you know,
and it's a government bid warden,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/287-2
<v Peter Mustow | Orro>the product. Yeah,
we have a we have a we have a problem</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/286-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/287-3
<v Peter Mustow | Orro>that came up when I first joined where a
customer,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/287-4
<v Peter Mustow | Orro>a government customer is going *******
because we sold them.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/288-0
<v Peter Mustow | Orro>Myglue,
which is an IT glue customer fronting</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/288-1
<v Peter Mustow | Orro>portal for their password management and
in the contract we said every employee</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/288-2
<v Peter Mustow | Orro>will get a Myglue personal vault, right?
And then the guys on boarded the customer,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/288-3
<v Peter Mustow | Orro>there were some admins,
they can add or remove users and we just</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/288-4
<v Peter Mustow | Orro>left.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/291-0
<v Peter Mustow | Orro>To their own accord to do whatever.
And yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/291-1
<v Peter Mustow | Orro>they obviously didn't know how to manage
it. They don't know how to add users.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/291-2
<v Peter Mustow | Orro>It has limited functionality. Also,
the data is not in this country and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/291-3
<v Peter Mustow | Orro>they're a government customer.
It's in the States or Singapore, so.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/289-0
<v Naythan Dawe | Orro>I.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/290-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/292-0
<v Peter Mustow | Orro>When I found this out, you know,
Hamish and I were connecting and we're</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/292-1
<v Peter Mustow | Orro>like running through all the problems
that we've got. And I just said, look,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/292-2
<v Peter Mustow | Orro>you know, I think we need to,
we need to do something, you know, um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/292-3
<v Peter Mustow | Orro>how about I look into something?
And he said, Yep, go for it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/292-4
<v Peter Mustow | Orro>So Bitwarden and um, yeah,
just self self hosting that.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/293-0
<v Peter Mustow | Orro>So the idea is that I iterate on this of
what I've come up with so far,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/293-1
<v Peter Mustow | Orro>make it a lot better so that then we have
three different tiers that customers can</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/293-2
<v Peter Mustow | Orro>choose from.
The benefit is we've got our repo here</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/293-3
<v Peter Mustow | Orro>that we can just deploy into a customer.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/294-0
<v Peter Mustow | Orro>If they're not a customer of ours,
we can onboard them as a customer and we</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/294-1
<v Peter Mustow | Orro>can sell them a subscription.
We can deploy the resources into the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/294-2
<v Peter Mustow | Orro>subscription,
so the cost of the resources we'll get</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/294-3
<v Peter Mustow | Orro>ticket for,
and then we can wrap it with an MMR to</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/294-4
<v Peter Mustow | Orro>then redeploy newer versions to that
customer.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/296-0
<v Peter Mustow | Orro>And go through a proper automated
pipeline to then deploy, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/296-1
<v Peter Mustow | Orro>new versions under change control and
approval gates and auditing and reporting</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/296-2
<v Peter Mustow | Orro>and all that good stuff to the customer
just gets a report at the end of the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/296-3
<v Peter Mustow | Orro>month saying you're all compliant.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/298-0
<v Peter Mustow | Orro>And we get our security team to validate
this code, check this code,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/295-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/298-1
<v Peter Mustow | Orro>make sure that you know our practices are
above board and they can rubber stamp it</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/297-0
<v Naythan Dawe | Orro>Yeah, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/298-2
<v Peter Mustow | Orro>as well.
Internal audit and then the next stage</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/298-3
<v Peter Mustow | Orro>with this is then to look at potentially
putting it in the Azure marketplace to</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/298-4
<v Peter Mustow | Orro>then make.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/299-0
<v Peter Mustow | Orro>What is it? No, it's a fourth.
It'll be a fourth income stream.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/299-1
<v Peter Mustow | Orro>So we've got Bit Warden licensing.
So every month we export the Bit Warden</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/299-2
<v Peter Mustow | Orro>license number,
we import it to our partner portal for</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/299-3
<v Peter Mustow | Orro>Bit Warden and then we make a ticket on
it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/299-4
<v Peter Mustow | Orro>We make the money off the off the
consumption of the resource.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/301-0
<v Peter Mustow | Orro>This is the customer spending in the
Azure subscription because we are their</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/301-1
<v Peter Mustow | Orro>CSP.
We're making recur revenue through</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/301-2
<v Peter Mustow | Orro>patching and managing it and some basic,
you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/301-3
<v Peter Mustow | Orro>maybe some some help with getting the the
extension installed into their Chrome</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/301-4
<v Peter Mustow | Orro>agent or deploying it into Intune,
whatever it could be.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/304-0
<v Peter Mustow | Orro>And then the 4th one is the marketplace
where we could potentially get net new</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/300-0
<v Naythan Dawe | Orro>8.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/304-1
<v Peter Mustow | Orro>customers from the from the marketplace
just through word of mouth.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/302-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/304-2
<v Peter Mustow | Orro>So it's for for revenue streams that I'm
trying to focus on and then I'm gonna</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/304-3
<v Peter Mustow | Orro>rinse and repeat this to other services
like AVD as an example.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/303-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/307-0
<v Peter Mustow | Orro>Um, Azure. Uh,
Azure Dev Box or Microsoft Dev Box for</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/307-1
<v Peter Mustow | Orro>developers. Um,
there's a few other services that we can</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/305-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/307-2
<v Peter Mustow | Orro>do. Um, you know, landing zones.
They've been done to death,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/307-3
<v Peter Mustow | Orro>but I still think we might need to look
at landing zones to a degree, right?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/307-4
<v Peter Mustow | Orro>And what that looks like in the new world.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/306-0
<v Naythan Dawe | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/308-0
<v Peter Mustow | Orro>But.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/310-0
<v Naythan Dawe | Orro>Yeah,
we still need landing zones is a classic</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/310-1
<v Naythan Dawe | Orro>example of customer going,
I don't know what I need,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/310-2
<v Naythan Dawe | Orro>you tell me what I need. And then you go,
okay, well, option one,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/309-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/310-3
<v Naythan Dawe | Orro>two and three with a different zero at
the end of it or whatever.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/313-0
<v Naythan Dawe | Orro>Starting number is all templated,
but then there's the customization on on</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/313-1
<v Naythan Dawe | Orro>top of it.
They should also like you know on that</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/311-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/313-2
<v Naythan Dawe | Orro>example is when I was at advanced I was
like OK,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/313-3
<v Naythan Dawe | Orro>are we actually going to take on a
customer that doesn't want to have a</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/313-4
<v Naythan Dawe | Orro>firewall?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/314-0
<v Naythan Dawe | Orro>No Azure firewall, no other firewall.
Like do we?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/312-0
<v Peter Mustow | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/314-1
<v Naythan Dawe | Orro>Is that a line in the sand for us? Yes,
it's an expensive appliance to run every</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/314-2
<v Naythan Dawe | Orro>month,
but do we want to be on the hook for</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/314-3
<v Naythan Dawe | Orro>everything that's there?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/315-0
<v Naythan Dawe | Orro>With no intelligence, you know, and.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/317-0
<v Peter Mustow | Orro>Yep, Yep, I 100% agree.
Because the the attack landscape is just</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/317-1
<v Peter Mustow | Orro>insane.
It's just insca and it's actually</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/316-0
<v Naythan Dawe | Orro>Hmm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/317-2
<v Peter Mustow | Orro>frightful. Like how easily, you know, Oro,
we could get compromised and our</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/317-3
<v Peter Mustow | Orro>customers are screwed.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/320-0
<v Naythan Dawe | Orro>That happens every day,
and that's one of the it's interesting</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/318-0
<v Peter Mustow | Orro>Do you know what I mean? Uh,
we're not doing much at that. Oh.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/320-1
<v Naythan Dawe | Orro>you say that because it's one of the
things that I, um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/320-2
<v Naythan Dawe | Orro>was not happy about at Zeta.
I could have compromised that network in</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/320-3
<v Naythan Dawe | Orro>the blink of an eye. They had no idea.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/319-0
<v Peter Mustow | Orro>Mm-hmm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/321-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/322-0
<v Peter Mustow | Orro>Cool.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/323-0
<v Peter Mustow | Orro>Yeah, well.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/324-0
<v Peter Mustow | Orro>We are, yeah, we're too.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/325-0
<v Naythan Dawe | Orro>Should be going for it because well.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/326-0
<v Peter Mustow | Orro>Yeah, it's an interesting one.
SOC 2 is more of a yeah, look,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/326-1
<v Peter Mustow | Orro>I don't disagree with you.
I think that we probably should be</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/326-2
<v Peter Mustow | Orro>competent in that and be able to deliver
it. Um, SOC 2 is a US thing. It's more,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/326-3
<v Peter Mustow | Orro>um,
what I found is if you're gearing up to</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/326-4
<v Peter Mustow | Orro>either sell or you need those
requirements like a lot of.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/328-0
<v Peter Mustow | Orro>Lot of, um, enterprises will go SOC too.
Um, don't know.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/328-1
<v Peter Mustow | Orro>It's a good question for cyber, but um,
yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/330-0
<v Naythan Dawe | Orro>It depends on how we're going to go for
business,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/330-1
<v Naythan Dawe | Orro>but an increasing amount of tenders are
um, uh must be 27, 27,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/329-0
<v Peter Mustow | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/330-2
<v Naythan Dawe | Orro>001 and uh and ideally.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/334-0
<v Naythan Dawe | Orro>SOC 2.
Now if we said we were essential eight</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/334-1
<v Naythan Dawe | Orro>level 2 and something else,
then that might be OK.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/332-0
<v Peter Mustow | Orro>OK.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/334-2
<v Naythan Dawe | Orro>But there's a ton of stuff there because
yes, all the big breaches,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/334-3
<v Naythan Dawe | Orro>they're coming through the supply chain.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/333-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/335-0
<v Naythan Dawe | Orro>Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/336-0
<v Naythan Dawe | Orro>Which means we need to be,
if we're selling those services,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/336-1
<v Naythan Dawe | Orro>we need to be squeaky clean as well.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/337-0
<v Peter Mustow | Orro>Absolutely.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/338-0
<v Naythan Dawe | Orro>But you and I have more than enough other
**** on our plates right now.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/341-0
<v Peter Mustow | Orro>Yes,
we need to literally build a practice. Um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/339-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/341-1
<v Peter Mustow | Orro>which is, which is fun.
It's gonna be awesome. Um. So yeah, look,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/340-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/341-2
<v Peter Mustow | Orro>that that gives you just a very high
level of sort of where we're at. Um, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/342-0
<v Peter Mustow | Orro>I'm looking forward to coming back and my
remit is not to continue where I'll be</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/342-1
<v Peter Mustow | Orro>leaving off in terms of helping put out
the fires and manage fires.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/343-0
<v Naythan Dawe | Orro>How many months did you say you're a four?
I know.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/344-0
<v Peter Mustow | Orro>It's only one month. Yeah. Yeah. So, um,
yeah. Look, if we look at the calendar,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/344-1
<v Peter Mustow | Orro>it'll be probably the second week of
November ish. So it'll be the 10th. Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/346-0
<v Peter Mustow | Orro>And I've said to Hamish as well, you know,
look, if things are burning, I'm, yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/346-1
<v Peter Mustow | Orro>he, he will, he will,
he will call my mobile and we'll have a</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/346-2
<v Peter Mustow | Orro>chat. But outside of that, I'm not. Yeah,
I'm looking forward to getting back to</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/346-3
<v Peter Mustow | Orro>actually focus on cause I'm really
looking forward to try and start to make</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/346-4
<v Peter Mustow | Orro>money for the business.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/345-0
<v Naythan Dawe | Orro>Mhm, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/348-0
<v Peter Mustow | Orro>I'm seeing so many screw ups from just
stupid mistakes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/348-1
<v Peter Mustow | Orro>It's costing us money and it's like.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/347-0
<v Naythan Dawe | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/350-0
<v Peter Mustow | Orro>It's just not good. It's not good.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/349-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/354-0
<v Naythan Dawe | Orro>Yeah, we need to sort that out,
but there's I have an increasing list and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/351-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/354-1
<v Naythan Dawe | Orro>I have an idea of where to start.
I need to talk to Hamish about when he</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/352-0
<v Peter Mustow | Orro>Hmm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/354-2
<v Naythan Dawe | Orro>wants to have conversations and start
making change.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/353-0
<v Peter Mustow | Orro>Oh.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/355-0
<v Naythan Dawe | Orro>Um and.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/356-0
<v Peter Mustow | Orro>I think he wants to do it as soon as you
get a feel for it, mate, because.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/358-0
<v Naythan Dawe | Orro>Oh, well, I'm, I'm, I'm ready. I'm like,
OK,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/357-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/358-1
<v Naythan Dawe | Orro>let's when are you gonna change reporting
lines? And, um, let's get started.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/360-0
<v Peter Mustow | Orro>Yeah, well, that can be,
that can be done in a fortnight. So yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/360-1
<v Peter Mustow | Orro>have a have a chat with whoever else you
need to. But at the moment, like,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/360-2
<v Peter Mustow | Orro>we've talked about this so much as well,
it's like.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/359-0
<v Naythan Dawe | Orro>I.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/362-0
<v Naythan Dawe | Orro>I'm good to go. I I.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/361-0
<v Peter Mustow | Orro>Yeah, yeah, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/363-0
<v Naythan Dawe | Orro>Hoover up information and analyze it and
go.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/364-0
<v Naythan Dawe | Orro>My.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/365-0
<v Naythan Dawe | Orro>My analytical I'm not an analyst,
but the way I connect dots between what</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/365-1
<v Naythan Dawe | Orro>other people may think is unrelated and
I've been careful.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/367-0
<v Naythan Dawe | Orro>I don't think I've really learned
anything new that I didn't already think</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/366-0
<v Peter Mustow | Orro>Hmm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/367-1
<v Naythan Dawe | Orro>on Tuesday,
but I'm sure about a lot of it stuff.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/367-2
<v Naythan Dawe | Orro>Actually, to be fair,
probably by the end of Monday,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/370-0
<v Peter Mustow | Orro>Yeah, you're very,
you're very fortunate to to have like</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/367-3
<v Naythan Dawe | Orro>but let's go with Tuesday. Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/370-1
<v Peter Mustow | Orro>Hamish's knowledge so far on everything
that he's picked up,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/370-2
<v Peter Mustow | Orro>everything that Dillon knows historically,
everything that I've, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/370-3
<v Peter Mustow | Orro>cause with with without that, like,
you know when.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/368-0
<v Naythan Dawe | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/369-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/371-0
<v Peter Mustow | Orro>Hamish is only a month ahead of me.
And when I came on board,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/371-1
<v Peter Mustow | Orro>Hamish was sort of just getting stuck
into stuff and like I came on board and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/371-2
<v Peter Mustow | Orro>there was a week of introduction and it
was actually it was a less day three.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/371-3
<v Peter Mustow | Orro>I was just chucked into it, you know,
Aaron and you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/371-4
<v Peter Mustow | Orro>a few of the other or Uh leadership teams
chucked me in meetings and I was just</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/371-5
<v Peter Mustow | Orro>like, wow, what the hell is going on?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/372-0
<v Peter Mustow | Orro>On anyway.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/373-0
<v Peter Mustow | Orro>OK.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/374-0
<v Naythan Dawe | Orro>So um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/379-0
<v Naythan Dawe | Orro>Just throwing back to something we were
talking about before documentation,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/375-0
<v Peter Mustow | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/379-1
<v Naythan Dawe | Orro>it's something we need,
something we need to sort out sooner</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/376-0
<v Peter Mustow | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/377-0
<v Peter Mustow | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/379-2
<v Naythan Dawe | Orro>rather than later and.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/378-0
<v Peter Mustow | Orro>Hmm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/383-0
<v Naythan Dawe | Orro>It needs to be minimum friction entry
point. Um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/380-0
<v Peter Mustow | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/383-1
<v Naythan Dawe | Orro>I don't think it can wait until you come
back,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/383-2
<v Naythan Dawe | Orro>so because I'm going to start putting
pressure on it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/381-0
<v Peter Mustow | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/382-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/384-0
<v Naythan Dawe | Orro>Um, one,
I need a platform that we can share stuff</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/384-1
<v Naythan Dawe | Orro>in readily. Um,
I love Confluence because it's</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/384-2
<v Naythan Dawe | Orro>documentation and meetings and agendas
and decisions, um, actions,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/384-3
<v Naythan Dawe | Orro>all the rest of it.
And if we end up using.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/386-0
<v Naythan Dawe | Orro>Jira, then we can link to the Jira boards,
but that's another tier and cost and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/386-1
<v Naythan Dawe | Orro>everything else. Also Trello,
Kanbans and and whatnot.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/385-0
<v Peter Mustow | Orro>Mm-hmm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/386-2
<v Naythan Dawe | Orro>I do take your point on you know if the
documentation is you know you can have.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/387-0
<v Naythan Dawe | Orro>A replicated repo on your laptop and
you've got it with you,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/387-1
<v Naythan Dawe | Orro>but the chance of confluence going
offline, given that we don't have it,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/387-2
<v Naythan Dawe | Orro>I ******* hope we don't have an ADFS
server, but maybe we do.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/388-0
<v Peter Mustow | Orro>No, we've got, uh, we've got,
we've got entra. So we're lucky, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/389-0
<v Naythan Dawe | Orro>Yeah, yeah, absolutely. But um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/388-1
<v Peter Mustow | Orro>But with customers that, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/391-0
<v Naythan Dawe | Orro>I'm not saying that it confluence is a
thing or that we'll even get approval for</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/390-0
<v Peter Mustow | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/391-1
<v Naythan Dawe | Orro>it,
but I'm thinking about the people that</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/391-2
<v Naythan Dawe | Orro>we're talking about employing.
They will be fine with it,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/391-3
<v Naythan Dawe | Orro>but then we've got the wider service desk
and service hump and other people that</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/391-4
<v Naythan Dawe | Orro>need to access.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/393-0
<v Naythan Dawe | Orro>Things that will not be able to use grip
to find a file that they want. Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/392-0
<v Peter Mustow | Orro>Yeah, Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/394-0
<v Naythan Dawe | Orro>So uh.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/395-0
<v Peter Mustow | Orro>Look, I'm I'm all good for any anything.
Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/396-0
<v Peter Mustow | Orro>Anything's better than IT glue in my
opinion at the moment.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/397-0
<v Naythan Dawe | Orro>Yeah, I had a look and it was just like,
super clunky.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/398-0
<v Peter Mustow | Orro>Yeah, I know it's got a search thing.
Like you can click on the customer site</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/398-1
<v Peter Mustow | Orro>and you hit the search bar and it does
like you can pull up keywords and it look</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/399-0
<v Naythan Dawe | Orro>Yeah. Do you know what the team? No,
the team leads are.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/398-2
<v Peter Mustow | Orro>it do. It does do a thing, right?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/401-0
<v Naythan Dawe | Orro>their team is calling them and asking
them where to find documents in it,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/400-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/401-1
<v Naythan Dawe | Orro>and the team leads have all these
favorites to go to where they want to</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/401-2
<v Naythan Dawe | Orro>find these documents because it takes too
long to get there otherwise.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/401-3
<v Naythan Dawe | Orro>So umm if that's the only thing we're
really using it for anymore,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/401-4
<v Naythan Dawe | Orro>and passwords, then let's get rid of the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/403-0
<v Naythan Dawe | Orro>Password thing implement something
enterprise grade. Um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/403-1
<v Naythan Dawe | Orro>now whether it's the warden for us like,
you know, I'm big fan, big fan of.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/402-0
<v Peter Mustow | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/403-2
<v Naythan Dawe | Orro>So who was it?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/405-0
<v Naythan Dawe | Orro>I've always heard it referred to as eat
your own dog food,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/404-0
<v Peter Mustow | Orro>Yes, yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/405-1
<v Naythan Dawe | Orro>but a vendor that I was talking to called
it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/405-2
<v Naythan Dawe | Orro>I prefer to say drink your own champagne.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/407-0
<v Peter Mustow | Orro>I like that one, actually. Yeah,
it'll be pretty difficult,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/406-0
<v Naythan Dawe | Orro>Yeah, yeah, yeah.
It's much to the first time I heard.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/407-1
<v Peter Mustow | Orro>pretty difficult to to, um,
to make your own champagne. But um, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/408-0
<v Naythan Dawe | Orro>Yes, but uh,
but at least it doesn't make me go uh</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/408-1
<v Naythan Dawe | Orro>'cause you know, the idea of, you know,
using what you support shouldn't make you</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/408-2
<v Naythan Dawe | Orro>want to hell.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/409-0
<v Naythan Dawe | Orro>Though also having said that,
I've seen what some people feed their</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/409-1
<v Naythan Dawe | Orro>dogs and it doesn't look half bad.
But yeah, um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/409-2
<v Naythan Dawe | Orro>a nice old stinking bone or a can of chum.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/411-0
<v Naythan Dawe | Orro>So yeah,
I we need to sort that out because I need</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/410-0
<v Peter Mustow | Orro>Yeah, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/411-1
<v Naythan Dawe | Orro>to get information that we do have out of
IT glue and a gap analysis on.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/412-0
<v Naythan Dawe | Orro>What is what documentation do we actually
have? What do we need that we're missing?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/412-1
<v Naythan Dawe | Orro>And start the process of getting that out
of people's heads.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/413-0
<v Peter Mustow | Orro>Yep, I I think at a high level,
just to recap,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/413-1
<v Peter Mustow | Orro>SharePoint I don't think is gonna go away.
So I think in terms of.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/414-0
<v Naythan Dawe | Orro>No,
but you get the documentation out of it,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/414-1
<v Naythan Dawe | Orro>you know.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/416-0
<v Peter Mustow | Orro>Yes, yeah. So if we, if we,
if we look at SharePoint as just a just a</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/416-1
<v Peter Mustow | Orro>Dropbox, whatever you want to call it,
right, that can be fine.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/415-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/416-2
<v Peter Mustow | Orro>Things that we need to come up with is a
standard file structure across all</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/416-3
<v Peter Mustow | Orro>customers whether we have.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/418-0
<v Peter Mustow | Orro>A customer name and when a new customer
comes on board,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/418-1
<v Peter Mustow | Orro>I was I I had a power automate thing I
was working on that to, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/418-2
<v Peter Mustow | Orro>have a form,
just Microsoft forms and then only</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/417-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/418-3
<v Peter Mustow | Orro>certain people have access to that being
us.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/420-0
<v Peter Mustow | Orro>Where we put the name of the customer in
and and then it complies to a naming</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/420-1
<v Peter Mustow | Orro>format which creates a team site. Yeah,
that then populates managed services</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/419-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/420-2
<v Peter Mustow | Orro>folder and a PS folder and with under
that it has all the all the folder</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/420-3
<v Peter Mustow | Orro>structures and subfolders and we can
eventually just get the files we need.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/421-0
<v Naythan Dawe | Orro>Mm-hmm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/423-0
<v Peter Mustow | Orro>That, um, that collaboration,
which is what we're lacking.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/423-1
<v Peter Mustow | Orro>What I loved about and what I love about
Slack is the instant interaction you can</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/422-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/423-2
<v Peter Mustow | Orro>have by dragging people in any which way.
And Teams, for some reason, I love Teams,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/423-3
<v Peter Mustow | Orro>but then I use Slack and Slack I love.
I've come back to Teams and there's so</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/423-4
<v Peter Mustow | Orro>many things that Teams just doesn't.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/424-0
<v Peter Mustow | Orro>Do well for me.
I'm finding myself just clicking</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/427-0
<v Naythan Dawe | Orro>It's it's not. Yeah,
it's just not as collaborative and and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/424-1
<v Peter Mustow | Orro>everywhere and.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/425-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/427-1
<v Naythan Dawe | Orro>that's coming from.
So I have never actually used Slack,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/426-0
<v Peter Mustow | Orro>Hm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/427-2
<v Naythan Dawe | Orro>but I have heard everywhere I've always
has always been a teams organization, but.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/431-0
<v Naythan Dawe | Orro>Uh,
so many people just like Slack is a lot</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/431-1
<v Naythan Dawe | Orro>more collaborative, a lot more community.
Um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/429-0
<v Peter Mustow | Orro>Yeah, just doesn't.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/431-2
<v Naythan Dawe | Orro>so one of the things to get around that.
This is one of the ways that I don't like.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/430-0
<v Peter Mustow | Orro>OK.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/432-0
<v Naythan Dawe | Orro>Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/435-0
<v Naythan Dawe | Orro>Teams works is the channels,
**** just disappears into a channel and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/433-0
<v Peter Mustow | Orro>Yeah, OK.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/435-1
<v Naythan Dawe | Orro>you create a new thread and a blah blah
blah. It's like it's not chatty.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/435-2
<v Naythan Dawe | Orro>So one of the things I will want to do.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/434-0
<v Peter Mustow | Orro>Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/437-0
<v Naythan Dawe | Orro>And I'll is create a group like you know
just to chat that is everyone because</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/437-1
<v Naythan Dawe | Orro>then when people talk it comes up and it
naturally will end up close to the top of</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/437-2
<v Naythan Dawe | Orro>the stack so that anybody that wants to
interact and.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/436-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/441-0
<v Naythan Dawe | Orro>Reach out to their other teams and every
you know like can and that that's how</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/438-0
<v Peter Mustow | Orro>OK.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/441-1
<v Naythan Dawe | Orro>I've done it before that it's so that
it's there and it's hey,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/439-0
<v Peter Mustow | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/441-2
<v Naythan Dawe | Orro>good morning everyone and look what my
cat did on the weekend and blah blah blah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/441-3
<v Naythan Dawe | Orro>you know like that social side that you
can also then call out and say, hey,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/440-0
<v Peter Mustow | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/441-4
<v Naythan Dawe | Orro>has anyone dealt with this before?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/443-0
<v Naythan Dawe | Orro>And it's in front of 30 people and
someone is likely to go, yeah, Naythan,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/443-1
<v Naythan Dawe | Orro>you know, or call them or whatever,
you know?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/442-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/446-0
<v Peter Mustow | Orro>Yep, yeah, I agree. And then, yeah,
how we set up those,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/446-1
<v Peter Mustow | Orro>those team sites as well. Um, you know,
with with, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/446-2
<v Peter Mustow | Orro>the documentation sharing,
you can just Add all those tabs into that</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/445-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/446-3
<v Peter Mustow | Orro>group and go from there. But um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/448-0
<v Naythan Dawe | Orro>Yeah, yeah, yeah.
And I really like that idea because then</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/448-1
<v Naythan Dawe | Orro>all of the chat that is to that customer
is there and anybody that gets added in</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/447-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/448-2
<v Naythan Dawe | Orro>the future can go back and see and search
and stuff.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/448-3
<v Naythan Dawe | Orro>Do we have any ruling that's knocking out
chat histories?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/450-0
<v Naythan Dawe | Orro>Like some organizations are implementing,
it gets deleted after 30 days or.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/449-0
<v Peter Mustow | Orro>Are you?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/452-0
<v Peter Mustow | Orro>I don't believe so. No,
I don't believe so.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/452-1
<v Peter Mustow | Orro>It's only those rules when you add
someone into the group for the first time,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/452-2
<v Peter Mustow | Orro>so you can allow them to see history or
start from new. Um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/451-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/452-3
<v Peter Mustow | Orro>I think it's just when you add a member
in.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/452-4
<v Peter Mustow | Orro>I don't believe we're deleting stuff
after six months. I could be wrong,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/452-5
<v Peter Mustow | Orro>it could be on the pipeline,
but I haven't seen any of it in any of my.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/453-0
<v Peter Mustow | Orro>My chats at the moment, but um, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/456-0
<v Naythan Dawe | Orro>OK, yeah, I haven't. I didn't.
I didn't see anything. I'm kind of like,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/456-1
<v Naythan Dawe | Orro>why would you like? But yeah,
because whenever I add anyone to a team</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/454-0
<v Peter Mustow | Orro>Hmm, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/456-2
<v Naythan Dawe | Orro>like that, I'm doing, you know,
add with all history.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/455-0
<v Peter Mustow | Orro>Yes. Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/457-0
<v Naythan Dawe | Orro>So that if they need to search or they
need to find or whatever, they can.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/458-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/460-0
<v Peter Mustow | Orro>So they sent you docmost.
These guys are kind of like an Atlassian.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/459-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/461-0
<v Peter Mustow | Orro>Um, you know,
equivalent I guess in terms of</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/461-1
<v Peter Mustow | Orro>documentation and stuff.
I don't know how it comes in in terms of</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/461-2
<v Peter Mustow | Orro>pricing, but um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/462-0
<v Peter Mustow | Orro>That was something that I found when I
was doing some some looking around. Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/463-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/465-0
<v Peter Mustow | Orro>So yeah, have a look at that.
That could be a good option. Um, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/465-1
<v Peter Mustow | Orro>it plays well with code.
You could plug some things into it to do</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/464-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/465-2
<v Peter Mustow | Orro>some things. And yeah, we can integrate,
you know, diagrams and mermaid diagrams.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/465-3
<v Peter Mustow | Orro>Excely Draw, Draw I/O.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/466-0
<v Peter Mustow | Orro>So yeah, it could be,
it could be a good alternative in terms</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/467-0
<v Naythan Dawe | Orro>Confluence import.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/466-1
<v Peter Mustow | Orro>of pricing and things for us.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/468-0
<v Peter Mustow | Orro>Yes, yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/470-0
<v Naythan Dawe | Orro>Yeah, we'd wanna have a look at the, uh,
the business one, obviously,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/470-1
<v Naythan Dawe | Orro>because of the SSO, um,
and the other stuff.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/469-0
<v Peter Mustow | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/472-0
<v Peter Mustow | Orro>They do have a self hosting version or we
could go the enterprise which is hosted</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/471-0
<v Naythan Dawe | Orro>But.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/475-0
<v Naythan Dawe | Orro>Just yeah, I I don't.
I'd rather not touch self-hosted for for</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/472-1
<v Peter Mustow | Orro>with them. Um, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/475-1
<v Naythan Dawe | Orro>anything like that cause you know to your
point you don't want it to go down.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/473-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/475-2
<v Naythan Dawe | Orro>Uh and also then we would definitely want
to check how long they've been around and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/474-0
<v Peter Mustow | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/475-3
<v Naythan Dawe | Orro>reliability and.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/476-0
<v Naythan Dawe | Orro>And all the rest of that as well and have
you run it through?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/477-0
<v Naythan Dawe | Orro>Have you actually tested it?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/479-0
<v Peter Mustow | Orro>No, not this product.
We could spin it up and have a play if</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/478-0
<v Naythan Dawe | Orro>Yeah, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/479-1
<v Peter Mustow | Orro>you want.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/483-0
<v Naythan Dawe | Orro>Yeah, I mean, just kick off a free trial.
No, it's it's the usability. I mean,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/480-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/483-1
<v Naythan Dawe | Orro>it looks like, yeah,
formatting's gonna be similar and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/483-2
<v Naythan Dawe | Orro>everything else.
But how good is the search?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/483-3
<v Naythan Dawe | Orro>Can you create actions?
What else can you do? You know, like,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/481-0
<v Peter Mustow | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/482-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/483-4
<v Naythan Dawe | Orro>you know, how do, how do we make it?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/484-0
<v Naythan Dawe | Orro>Easy.
And that's one of the things I like about</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/484-1
<v Naythan Dawe | Orro>confluence. It's so easy. It doesn't.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/485-0
<v Peter Mustow | Orro>Yeah, because you can.
You can work on everything together and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/486-0
<v Naythan Dawe | Orro>Yeah, yeah. And we, you know, in my head,
eventually once we've got it,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/485-1
<v Peter Mustow | Orro>collaborate. Yeah, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/486-1
<v Naythan Dawe | Orro>is that OTC or something that sits
outside OTC but has access to the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/486-2
<v Naythan Dawe | Orro>incidents and everything else can either.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/488-0
<v Naythan Dawe | Orro>Work directly with it. In my opinion,
OTC now needs to be under a strangler</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/488-1
<v Naythan Dawe | Orro>pattern. No more development,
get the external API up and running and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/488-2
<v Naythan Dawe | Orro>build new micro services and outside it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/487-0
<v Peter Mustow | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/490-0
<v Peter Mustow | Orro>It's been around for a long time,
OTC and I think it's just, yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/489-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/490-1
<v Peter Mustow | Orro>I think they've invested,
the business has invested too much into</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/490-2
<v Peter Mustow | Orro>it to a degree and now they've just
thrown a lot more money at it now with</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/490-3
<v Peter Mustow | Orro>everything that Jono's been proving the
business.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/491-0
<v Peter Mustow | Orro>Can be done with, you know,
not as many people per se. Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/491-1
<v Peter Mustow | Orro>So then they're like, oh,
let's just do it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/491-2
<v Peter Mustow | Orro>We'll get Claude to uplift OTC and anyway.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/494-0
<v Naythan Dawe | Orro>But that's that's that's not the way.
It's not the way most places.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/492-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/494-1
<v Naythan Dawe | Orro>That's how the if they want it to fail,
that's how it happens that.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/493-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/494-2
<v Naythan Dawe | Orro>But I don't think Jono is on the and I
haven't had detailed conversations.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/494-3
<v Naythan Dawe | Orro>He might be coming in tomorrow.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/495-0
<v Naythan Dawe | Orro>It sounds like China and Gina are leaning
towards strangler pattern as in</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/495-1
<v Naythan Dawe | Orro>deprecated as much as possible and new
like an update and patch and everything</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/495-2
<v Naythan Dawe | Orro>else, but all new features happen outside.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/502-0
<v Naythan Dawe | Orro>They'll happen a lot quicker.
Time to market MVP so much quicker.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/496-0
<v Peter Mustow | Orro>Hmm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/502-1
<v Naythan Dawe | Orro>No risk to take down core billing because
that's always how this happens.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/497-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/502-2
<v Naythan Dawe | Orro>It becomes the core of something and it's
tied into billing.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/498-0
<v Peter Mustow | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/502-3
<v Naythan Dawe | Orro>And so it's a three to four months
development pattern.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/499-0
<v Peter Mustow | Orro>Yep, Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/502-4
<v Naythan Dawe | Orro>It has to be order four.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/503-0
<v Naythan Dawe | Orro>It can't be anything else. Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/500-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/501-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/504-0
<v Naythan Dawe | Orro>So hang on.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/505-0
<v Naythan Dawe | Orro>Didn't mute properly. How did you?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/506-0
<v Peter Mustow | Orro>No, no, that's OK. All good.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/507-0
<v Naythan Dawe | Orro>Um, uh, so anyway, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/508-0
<v Peter Mustow | Orro>Yeah, well, if confluence, I'm, I'm all,
I'm all on board with it. It's just,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/510-0
<v Naythan Dawe | Orro>And if this other thing works and it's
easy to use and everything else and it's</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/508-1
<v Peter Mustow | Orro>you know, when and how and.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/509-0
<v Peter Mustow | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/510-1
<v Naythan Dawe | Orro>cheaper, I don't really care.
I'm not fussy as long as we can access it</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/510-2
<v Naythan Dawe | Orro>through. If it's cloud hosted,
that's fine.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/510-3
<v Naythan Dawe | Orro>I'll be able to get my agent to post to
it just like I do normally.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/510-4
<v Naythan Dawe | Orro>I'm testing with.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/512-0
<v Naythan Dawe | Orro>Mind to rag the pages that are there and
everything else that whatever.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/512-1
<v Naythan Dawe | Orro>But whatever we do,
it needs to be repeatable and easy and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/511-0
<v Peter Mustow | Orro>100%.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/512-2
<v Naythan Dawe | Orro>easy to get the answers,
including like I'm I'm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/513-0
<v Naythan Dawe | Orro>Thinking from a.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/514-0
<v Naythan Dawe | Orro>In fact, thinking about it,
I already know a platform that would help</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/514-1
<v Naythan Dawe | Orro>us with a lot of these problems now.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/515-0
<v Peter Mustow | Orro>Oh, thank you.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/532-0
<v Peter Mustow | Orro>Hey, no.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/533-0
<v Peter Mustow | Orro>Just free power power on off.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/534-0
<v Peter Mustow | Orro>I'm guessing you can hear me.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/535-0
<v Peter Mustow | Orro>OK.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/537-0
<v Peter Mustow | Orro>2.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/539-0
<v Peter Mustow | Orro>No, nothing.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/541-0
<v Naythan Dawe | Orro>Now.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/542-0
<v Peter Mustow | Orro>Yes, I pay now.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/544-0
<v Naythan Dawe | Orro>My phone rang,
took over the base station 'cause I um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/547-0
<v Peter Mustow | Orro>Yeah, I thought that's what happened.
Mine does that sometimes too with my</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/546-0
<v Naythan Dawe | Orro>End.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/547-1
<v Peter Mustow | Orro>mobile.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/551-0
<v Naythan Dawe | Orro>But then normally when I hang up,
it just like, you know, kill it,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/548-0
<v Peter Mustow | Orro>Tell us back.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/551-1
<v Naythan Dawe | Orro>it goes straight back.
But I had to cycle the power on the base</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/549-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/551-2
<v Naythan Dawe | Orro>station to to get it back and like and I
switched the, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/550-0
<v Peter Mustow | Orro>That that's OK.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/551-3
<v Naythan Dawe | Orro>the local speaker and mic and then back
and whatever, so.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/554-0
<v Peter Mustow | Orro>When you picked up your phone like that
and then you put it down and the audio</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/554-1
<v Peter Mustow | Orro>went, I'm like, uh, he's tethered to both.
And I've been there, man. I've been there.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/552-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/553-0
<v Naythan Dawe | Orro>So annoying, but anyway, um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/554-2
<v Peter Mustow | Orro>All good, all good.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/555-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/557-0
<v Peter Mustow | Orro>Yeah, look, I think we'll get there.
I think we'll get there. Um, yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/557-1
<v Peter Mustow | Orro>I think once we work out the core of,
you know, what what works best.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/557-2
<v Peter Mustow | Orro>And if you've got things that have worked
before,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/557-3
<v Peter Mustow | Orro>I'm more than happy to test things out.
I'll spin up a demo of this thing,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/557-4
<v Peter Mustow | Orro>cause like I said,
I've never taken it for a spin.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/556-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/558-0
<v Peter Mustow | Orro>I'll see what we can do with it. Um,
I'll let you know if I think it's OK or</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/558-1
<v Peter Mustow | Orro>if it's ****. Um, yeah,
we can go from there.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/560-0
<v Naythan Dawe | Orro>Cool. Um. And.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/559-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/562-0
<v Naythan Dawe | Orro>Because I was actually thinking reach out
to like to the contact us for confluence.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/561-0
<v Peter Mustow | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/563-0
<v Naythan Dawe | Orro>And I'll talk to them and actually find
out what pricing is like,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/563-1
<v Naythan Dawe | Orro>'cause I think they're pretty.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/565-0
<v Naythan Dawe | Orro>Kidden now.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/564-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/566-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/567-0
<v Naythan Dawe | Orro>I'd had a look earlier and I couldn't see
it, so.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/568-0
<v Naythan Dawe | Orro>And that way we've got some information
'cause there's other products out there</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/568-1
<v Naythan Dawe | Orro>that help us with other things, but.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/569-0
<v Naythan Dawe | Orro>I mean, if we were going to use Jira,
it would probably be a number brainer,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/569-1
<v Naythan Dawe | Orro>but I don't know that.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/570-0
<v Naythan Dawe | Orro>It is.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/571-0
<v Naythan Dawe | Orro>So.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/572-0
<v Peter Mustow | Orro>Yeah, I I do love Jiro.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/573-0
<v Peter Mustow | Orro>It is very good. It's so quick.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/574-0
<v Naythan Dawe | Orro>If if you were picking anything,
is that what you would pick for us to use?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/575-0
<v Peter Mustow | Orro>Yeah, look,
I think that's through things that I've</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/575-1
<v Peter Mustow | Orro>been able to do with Jira, uh,
including the service desk in terms of</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/575-2
<v Peter Mustow | Orro>tickets and um,
just your different groups and like,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/575-3
<v Peter Mustow | Orro>there's nothing you can't not do now with
Kate query in terms of like the.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/576-0
<v Peter Mustow | Orro>Like the dashboard setups and things like
that, the different queues.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/576-1
<v Peter Mustow | Orro>I've used it as a service desk tool as
well with DSH.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/576-2
<v Peter Mustow | Orro>So it was literally just e-mail
automations that came in and it just.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/577-0
<v Peter Mustow | Orro>Yeah, went into a group,
it was categorized and then it went went</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/577-1
<v Peter Mustow | Orro>through a a ticket workflow which was
created, um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/577-2
<v Peter Mustow | Orro>just for standard service requests and
incidents and things like that. Um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/577-3
<v Peter Mustow | Orro>it was great and reporting category
classifications.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/579-0
<v Peter Mustow | Orro>Um,
then you can get all your statistics on,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/579-1
<v Peter Mustow | Orro>you know, um,
tickets touched and all that kind of cool</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/579-2
<v Peter Mustow | Orro>stuff. Like,
you know how long it took to complete the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/579-3
<v Peter Mustow | Orro>ticket. You know, if you,
if you met with first response,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/579-4
<v Peter Mustow | Orro>if you break, if you broke SLA,
if you're coming up to SLA,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/578-0
<v Naythan Dawe | Orro>Mm-hmm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/579-5
<v Peter Mustow | Orro>all those kind of things, it was really,
really good.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/581-0
<v Peter Mustow | Orro>Um, I just found ServiceNow,
and it might have been, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/581-1
<v Peter Mustow | Orro>when I used it many years ago,
but I just found it a bit kind of.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/581-2
<v Peter Mustow | Orro>I can never get my head around ServiceNow.
I don't know, it's great,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/580-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/581-3
<v Peter Mustow | Orro>but I just found JIRA worked a lot better
for me. Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/583-0
<v Peter Mustow | Orro>I got really used to the shortcuts as
well,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/583-1
<v Peter Mustow | Orro>so I was really able to just jump to the
fields and do what I needed to do,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/583-2
<v Peter Mustow | Orro>just by shortcuts.
I didn't have to touch the mouse really</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/583-3
<v Peter Mustow | Orro>on a ticket at the end of it,
and I was just, yeah, internal comments,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/582-0
<v Naythan Dawe | Orro>So.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/583-4
<v Peter Mustow | Orro>adding people. Uh, it's a lot better.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/585-0
<v Naythan Dawe | Orro>And a are you referring to it in a
ticketing sense or and and what about a</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/584-0
<v Peter Mustow | Orro>Ticketing sense.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/585-1
<v Naythan Dawe | Orro>development platform?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/586-0
<v Peter Mustow | Orro>Yeah, so normal Kanban.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/589-0
<v Naythan Dawe | Orro>Yeah,
and backlog and um sprints and all the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/587-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/589-1
<v Naythan Dawe | Orro>rest.
Do you envisage us do doing that sort of</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/588-0
<v Peter Mustow | Orro>Yes, we did backlogs through it sprints.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/589-2
<v Naythan Dawe | Orro>work in the future?
Do we need something like that or is it a?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/590-0
<v Naythan Dawe | Orro>Overkill.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/591-0
<v Naythan Dawe | Orro>So we we get the support stuff,
we've got tickets going into OTC,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/591-1
<v Naythan Dawe | Orro>but we've also got the engineering aspect
of the five hours a month,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/591-2
<v Naythan Dawe | Orro>five days a month, 10 days a month,
whatever for.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/593-0
<v Naythan Dawe | Orro>The continual improvement stuff,
not projects, but you know, but then uh,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/593-1
<v Naythan Dawe | Orro>if we had something like that,
then I would want the project to go into</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/593-2
<v Naythan Dawe | Orro>that as well and not be managed out of it.
Would we do, would we do it in?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/592-0
<v Peter Mustow | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/596-0
<v Naythan Dawe | Orro>Because I don't I we we definitely don't
have project management and backlogs in</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/594-0
<v Peter Mustow | Orro>OK.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/596-1
<v Naythan Dawe | Orro>OTC and I wouldn't want to try.
So we need something for in the future.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/595-0
<v Peter Mustow | Orro>No, no, at at the moment.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/596-2
<v Naythan Dawe | Orro>We are going to need something with that
something in that space.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/597-0
<v Naythan Dawe | Orro>Given that we already have a service desk,
we won't be taking on Atlassians.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/597-1
<v Naythan Dawe | Orro>Would that something for you be Jira or
would it be something else?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/598-0
<v Peter Mustow | Orro>It would be a Jira or a Jira equivalent,
yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/599-0
<v Naythan Dawe | Orro>In which case.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/604-0
<v Naythan Dawe | Orro>Confluence and Jira because then you link
the knowledge base articles.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/600-0
<v Peter Mustow | Orro>Yeah, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/601-0
<v Peter Mustow | Orro>Yeah, yeah,
you can reference ticket history and.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/604-1
<v Naythan Dawe | Orro>Then you have the Trello Kanban boards
and blah blah blah. Well,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/604-2
<v Naythan Dawe | Orro>not so much ticketing. Yeah,
you're talking about, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/604-3
<v Naythan Dawe | Orro>epics and epics and tasks and stuff.
Are you talking about? OK, OK,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/602-0
<v Peter Mustow | Orro>I'm talking about when I tag.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/603-0
<v Peter Mustow | Orro>Yeah, epics and tasks, yeah,
but but then they.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/604-4
<v Naythan Dawe | Orro>so I just wanted because of course.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/605-0
<v Naythan Dawe | Orro>Jira also has its Service Desk element.
I wanted to make sure you're talking</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/605-1
<v Naythan Dawe | Orro>about Jira, not Jira Service Desk.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/607-0
<v Peter Mustow | Orro>Both. I've worked with both, yeah,
but in a ticket, yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/606-0
<v Naythan Dawe | Orro>Yeah, but would we? Yes,
but would we use both?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/607-1
<v Peter Mustow | Orro>so in a ticket you can automate that.
So with the automation with a ticket,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/607-2
<v Peter Mustow | Orro>you can now get the service requests
analyzed and referenced back to a KB</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/607-3
<v Peter Mustow | Orro>which.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/609-0
<v Peter Mustow | Orro>Influence can then link into the ticket.
Do you get what I mean?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/608-0
<v Naythan Dawe | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/609-1
<v Peter Mustow | Orro>So you're able to cross reference things
that and share with users on the ticket</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/609-2
<v Peter Mustow | Orro>that information as well.
But I'm only talking about a customer</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/609-3
<v Peter Mustow | Orro>where I had this working perfectly that
could consume.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/610-0
<v Peter Mustow | Orro>The JIRA as well.
If you're talking about a customer that</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/610-1
<v Peter Mustow | Orro>is like we're doing at the moment,
they've got their ServiceNow and we're</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/610-2
<v Peter Mustow | Orro>just into us and then we're replying and
it goes in their ServiceNow.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/610-3
<v Peter Mustow | Orro>They're not going to be able to click on
our KB for our confluence and then have</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/610-4
<v Peter Mustow | Orro>access to that, so.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/612-0
<v Peter Mustow | Orro>That part I haven't under.
I haven't been involved in any of that</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/612-1
<v Peter Mustow | Orro>stuff. So I don't actually know. You know,
we wouldn't be able to at tag someone at</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/612-2
<v Peter Mustow | Orro>the customer to check something.
Do you know what I mean?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/612-3
<v Peter Mustow | Orro>Like you could if we're in ServiceNow,
we can at tag.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/611-0
<v Naythan Dawe | Orro>The um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/613-0
<v Peter Mustow | Orro>'Cause it's not looking them up is what
I'm trying to say,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/613-1
<v Peter Mustow | Orro>'cause it's referencing,
it's referencing internal, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/614-0
<v Naythan Dawe | Orro>Yeah, well, I just, I, I yeah, yeah, yeah,
I just. I mean, like I said, if, if,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/614-1
<v Naythan Dawe | Orro>if the full OTC move hadn't just happened.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/615-0
<v Naythan Dawe | Orro>I would have really wanted to understand
why it happened and.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/618-0
<v Peter Mustow | Orro>We had no choice. We had,
we had no choice to a degree. I think,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/616-0
<v Naythan Dawe | Orro>And well, that's that's the thing.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/618-1
<v Peter Mustow | Orro>I think Naythan,
I think Naythan had already teed that up</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/618-2
<v Peter Mustow | Orro>in that direction through the the
pressure he was getting or whatever the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/618-3
<v Peter Mustow | Orro>business was trying to get on board for
that. But as you as you are well aware,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/618-4
<v Peter Mustow | Orro>it has taken us a step back because it
would have just had all those.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/619-0
<v Peter Mustow | Orro>That it was a help desk tool.
We had all that functionality to a degree,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/617-0
<v Naythan Dawe | Orro>Was it?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/619-1
<v Peter Mustow | Orro>right?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/620-0
<v Naythan Dawe | Orro>So was it just a?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/621-0
<v Naythan Dawe | Orro>Rice decision.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/622-0
<v Peter Mustow | Orro>I've got no idea.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/624-0
<v Peter Mustow | Orro>I've got no idea if it was price.
I know that one of the cyber teams have</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/623-0
<v Naythan Dawe | Orro>Because I'd.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/624-1
<v Peter Mustow | Orro>still got their service desk.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/625-0
<v Peter Mustow | Orro>So they were like, no, FFOTC.
We're not doing it until XYZ and they</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/625-1
<v Peter Mustow | Orro>they have Fresh Drive or whatever the
hell it is, not even a Freshdesk. Um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/625-2
<v Peter Mustow | Orro>so they use their separate ticketing
system and then we obviously had NWS and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/625-3
<v Peter Mustow | Orro>then.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/627-0
<v Peter Mustow | Orro>Yeah, it got, it got moved. So yeah,
and they had all the like The thing is</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/627-1
<v Peter Mustow | Orro>with the Kaseya products, it would,
it would have kept us in that ecosystem</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/627-2
<v Peter Mustow | Orro>for a bit longer because like as I said,
Kaseya has,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/627-3
<v Peter Mustow | Orro>Kaseya has like inventory management and
all these kind of, you know,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/626-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/627-4
<v Peter Mustow | Orro>add-ons and it just snaps into Autodesk.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/630-0
<v Peter Mustow | Orro>So a customer can reply and we can just
go at infantry and it just grabs the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/630-1
<v Peter Mustow | Orro>information, puts it in the ticket, send,
it goes off to the customer and they've</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/628-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/630-2
<v Peter Mustow | Orro>got real data and like it's actually not
too bad. It's just not super great. Um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/629-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/630-3
<v Peter Mustow | Orro>but yeah,
and I just embed you more in their in</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/630-4
<v Peter Mustow | Orro>their process, uh and their tool.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/632-0
<v Peter Mustow | Orro>But yeah, look,
I think a confluence in a JIRA,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/632-1
<v Peter Mustow | Orro>if we had to, that would be my direction.
No brainer if I had to set up tool sets</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/632-2
<v Peter Mustow | Orro>because like, yeah, it's easy to use.
Everyone will understand it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/631-0
<v Naythan Dawe | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/633-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/635-0
<v Peter Mustow | Orro>Just don't know how it fits in the OTC
thing at the moment.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/635-1
<v Peter Mustow | Orro>How much work would we need to do to
integrate it into OTC to then? Yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/634-0
<v Naythan Dawe | Orro>OK.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/635-2
<v Peter Mustow | Orro>I don't know.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/637-0
<v Naythan Dawe | Orro>I I wouldn't integrate it into OTC.
That's that's the thing.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/636-0
<v Peter Mustow | Orro>OK.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/638-0
<v Naythan Dawe | Orro>Why would we need to integrate and we
need to look at what we're doing there</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/638-1
<v Naythan Dawe | Orro>and that's why I was very careful about
what I was saying about service desk,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/638-2
<v Naythan Dawe | Orro>which is what OTC is primarily therefore
looks like versus.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/643-0
<v Naythan Dawe | Orro>DevOps because you wouldn't run DevOps
through a service desk.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/639-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/643-1
<v Naythan Dawe | Orro>It's different and it wouldn't work.
I was talking to Jackie earlier and I'm</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/640-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/641-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/642-0
<v Peter Mustow | Orro>Yep.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/643-2
<v Naythan Dawe | Orro>like, well.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/644-0
<v Naythan Dawe | Orro>The pods are not going to be.
They might be idle light,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/644-1
<v Naythan Dawe | Orro>but they will not be idle.
The principles will be there and the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/644-2
<v Naythan Dawe | Orro>guardrails,
but and I was talking really gentle,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/644-3
<v Naythan Dawe | Orro>just in case.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/645-0
<v Peter Mustow | Orro>1.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/647-0
<v Naythan Dawe | Orro>Because she she is one of the few people
that I have heard say negative things</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/646-0
<v Peter Mustow | Orro>Yes.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/647-1
<v Naythan Dawe | Orro>about people in the business.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/648-0
<v Naythan Dawe | Orro>So it's like, OK.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/649-0
<v Peter Mustow | Orro>Mhm.
Wants to know all about you and how much</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/649-1
<v Peter Mustow | Orro>you know.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/652-0
<v Naythan Dawe | Orro>And not backwards providing her opinion
on many things. Um, uh, so anyway.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/651-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/654-0
<v Naythan Dawe | Orro>Yeah, I think we need something.
We need to work out how to integrate it.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/654-1
<v Naythan Dawe | Orro>It's also why I asked all the questions
about how much development is actually</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/654-2
<v Naythan Dawe | Orro>going on in OTC,
because once the API gateway is there</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/654-3
<v Naythan Dawe | Orro>with all the other stuff,
there is nothing if we can get it if they</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/653-0
<v Peter Mustow | Orro>Mm yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/654-4
<v Naythan Dawe | Orro>want to do it this way that says as
people.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/656-0
<v Naythan Dawe | Orro>Start selecting what the category is of a
ticket that comes in and then start</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/656-1
<v Naythan Dawe | Orro>actually writing what the customer is
saying or automatically transcribing it</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/656-2
<v Naythan Dawe | Orro>and putting it in there,
which is why I'm a little bit oh ****</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/656-3
<v Naythan Dawe | Orro>that we're using OTC.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/655-0
<v Peter Mustow | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/658-0
<v Naythan Dawe | Orro>But because the other platforms will be
doing that now, but if we can do it,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/658-1
<v Naythan Dawe | Orro>that there's something outside it that's
doing it and automatically whatever,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/658-2
<v Naythan Dawe | Orro>you know, so much as possible.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/657-0
<v Peter Mustow | Orro>Yeah, please.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/662-0
<v Naythan Dawe | Orro>Because I all of that calls should be
coded and transcribed and automatic,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/659-0
<v Peter Mustow | Orro>Oh, absolutely, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/662-1
<v Naythan Dawe | Orro>you know like and summarized and and put
in there like all all of the problems</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/660-0
<v Peter Mustow | Orro>All our all our.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/662-2
<v Naythan Dawe | Orro>we're seeing disappear and it and and it
knocks out level one.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/662-3
<v Naythan Dawe | Orro>But as that starts coming up then the
next agent goes and says.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/661-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/664-0
<v Naythan Dawe | Orro>What have I got? You know,
confluence ragged instant answers.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/664-1
<v Naythan Dawe | Orro>Have you tried? Have you tried?
Have you tried? Boom, boom, boom, boom,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/663-0
<v Peter Mustow | Orro>Mhm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/665-0
<v Peter Mustow | Orro>Yep, Yep.
Or or or I already know the answer to</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/664-2
<v Naythan Dawe | Orro>boom.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/665-1
<v Peter Mustow | Orro>this. Then reference and post and send.
Done. Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/666-0
<v Naythan Dawe | Orro>Yeah, yeah.
And to your point about sharing it and</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/666-1
<v Naythan Dawe | Orro>everything else, well,
then you just have it in a, um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/666-2
<v Naythan Dawe | Orro>external face. This is a thing though.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/667-0
<v Naythan Dawe | Orro>You don't really want your KBS fully
externally accessible, but.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/668-0
<v Peter Mustow | Orro>No,
but this is this is what I've been told</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/668-1
<v Peter Mustow | Orro>is the direction though of what their
plans are uh for KBS in OTC is that the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/668-2
<v Peter Mustow | Orro>KB articles can be linked to tickets and
customers can see KBS.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/669-0
<v Peter Mustow | Orro>Um, anyway.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/672-0
<v Peter Mustow | Orro>Take, take it,
take it as far as you need to.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/672-1
<v Peter Mustow | Orro>I've I've been staying away from the OTC
conversations merely cause I just haven't</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/672-2
<v Peter Mustow | Orro>had time to get involved in another thing
as well. Um. But yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/670-0
<v Naythan Dawe | Orro>Mm.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/672-3
<v Peter Mustow | Orro>I'm more than happy to sit and work
something out with you on it if we need</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/672-4
<v Peter Mustow | Orro>to, but um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/671-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/674-0
<v Peter Mustow | Orro>Yeah,
I definitely think that we need to align</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/674-1
<v Peter Mustow | Orro>with tools that empower us to do our job
better, um,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/674-2
<v Peter Mustow | Orro>and not have to ask for feature requests
and wait for when they're delivered.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/673-0
<v Naythan Dawe | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/676-0
<v Peter Mustow | Orro>Yeah. Anyway, Yep, beautiful. Um, yeah.
So I can probably send through.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/675-0
<v Naythan Dawe | Orro>Alright.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/676-1
<v Peter Mustow | Orro>I'll send through this transcribe and
then we'll work out anything else.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/676-2
<v Peter Mustow | Orro>If there's anything that you've have a
think about that you need some answers on,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/676-3
<v Peter Mustow | Orro>um, let me know.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/677-0
<v Peter Mustow | Orro>Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/679-0
<v Peter Mustow | Orro>And I can, um,
I can get those for you as soon as I can.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/678-0
<v Naythan Dawe | Orro>Cool.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/679-1
<v Peter Mustow | Orro>Um.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/681-0
<v Naythan Dawe | Orro>Can you send me the full transcripts for
this one and the previous one as well?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/680-0
<v Peter Mustow | Orro>Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/682-0
<v Peter Mustow | Orro>Yes, I can send you.
I'll download the VTT's and I'll send</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/681-1
<v Naythan Dawe | Orro>I want to run them through my AI and and
compare them.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/682-1
<v Peter Mustow | Orro>them through.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/683-0
<v Naythan Dawe | Orro>Cool. No,
you you should actually just be able to</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/683-1
<v Naythan Dawe | Orro>download the transcript.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/684-0
<v Naythan Dawe | Orro>Can you?</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/685-0
<v Peter Mustow | Orro>Yes, it gives me the summary. Yeah.
So I can get the summary and I can get</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/685-1
<v Peter Mustow | Orro>the, um,
I'll just go to our other meeting.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/685-2
<v Peter Mustow | Orro>Hang on.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/686-0
<v Naythan Dawe | Orro>'Cause I think you'd be able to download
the actual transcript rather than the</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/686-1
<v Naythan Dawe | Orro>full recording. VTT,
you were referring to the recording of it,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/690-0
<v Peter Mustow | Orro>Yes, uh, the VTT is just the um,
that's the text text equivalent format.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/686-2
<v Naythan Dawe | Orro>right? Yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/687-0
<v Naythan Dawe | Orro>Oh, is it? OK, yeah,
that's that's what I'm talking about.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/690-1
<v Peter Mustow | Orro>Cause oh, have you used?
Have you used O O meeting? Yeah,</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/687-1
<v Naythan Dawe | Orro>Sorry, don't worry about me.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/690-2
<v Peter Mustow | Orro>O meeting. Yes. OK,
let me just send you the files.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/688-0
<v Naythan Dawe | Orro>No, but I want to give it a go.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/690-3
<v Peter Mustow | Orro>If they're not the ones you want,
I'll send you the doc or whatever it</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/689-0
<v Naythan Dawe | Orro>Hmm, yeah.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/690-4
<v Peter Mustow | Orro>gives.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/692-0
<v Peter Mustow | Orro>me out of Copilot.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/691-0
<v Naythan Dawe | Orro>OK, cool.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/694-0
<v Peter Mustow | Orro>Beautiful. OK, enjoy your night. I'll uh,
I'll chat with you tomorrow.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/693-0
<v Naythan Dawe | Orro>Thank you.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/695-0
<v Naythan Dawe | Orro>OK, see ya.</v>
e690f94e-b4de-4119-bbbf-ec73c6427cac/697-0
<v Peter Mustow | Orro>OK. See ya. Bye.</v>

---

*Generated by Maia VTT Watcher with FOB Templates + Local LLM Intelligence (CodeLlama 13B)*
*Framework: Technical Discussion | Cost Savings: 99.3% vs cloud LLMs | Carbon Neutral: 100% local*
*Location: /Users/naythandawe/git/maia/claude/data/transcript_summaries*
