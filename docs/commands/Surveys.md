---
layout: default
title: Surveys
parent: Commands
nav_order: 9
---
		
<h1>Surveys</h1>
<h6>version: 3.2</h6>
<h6>Documentation automatically generated from docstrings.</h6>

This module helps you gather valuable feedback from members who decide to leave your server.
When a member leaves, this system can automatically send them a direct message with a link to a feedback survey.
This feature is only active for premium servers and can be enabled or disabled through the configuration settings.
There are no user-runnable commands in this module; it all works in the background!


### `on_member_remove`

**Usage:** `/surveys on_member_remove <member>`

> This event handler sends the survey to the user when they leave the server.

---

