# Silent Curriculum — Forensics Q&A

A WordPress learning platform showed signs of account takeover. You are given a
single packet capture of the incident window.

Analyze `silent_curriculum.pcap` and answer these 10 questions.

1. What source IP address performed the main intrusion?
2. What WordPress plugin was investigated immediately before the SQL injection activity?
3. What REST endpoint was targeted by the SQL injection?
4. Which query-string parameter was used as the injection point?
5. What SQL injection technique was primarily used to enumerate data?
6. Which WordPress database table did the attacker target for credential data?
7. Which WordPress account was used for the successful administrative login?
8. What backdoor filename was later accessed to execute commands?
9. What email address did the attacker use when creating the rogue administrator account?
10. At what exact UTC timestamp was the rogue administrator account created?

## Answer format
Use short answers. For question 10, format the packet timestamp of the account-creation
request as an Apache combined-log stamp, e.g. `25/Sep/2024:HH:MM:SS +0000`.
