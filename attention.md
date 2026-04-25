# Research Article: Multi-Model Ensemble Deliberation with Graph Neural Network Integration for Explainable Clinical Biomarker Analysis in Oncology

**Subject:** Biomedical Informatics / Artificial Intelligence in Medicine / Trustworthy AI  
**Draft Version:** 1.0.6 - Optimized for Clinical Submission

---

## Abstract

Modern medicine has many high-tech tools to find cancer, but doctors often find them hard to trust because they don't explain how they work. This study introduces a new "Clinical Dashboard" that helps solve this problem. Our system uses a group of different AI programs—which we call an "Expert Committee"—to look at blood test results together. We also use a special mapping tool to see how different markers in the blood (like PSA and AFP) connect to each other. By using these methods, our system doesn't just give an answer; it explains its reasoning and shows "What-If" scenarios to help doctors plan treatment. This approach makes computer-aided diagnosis much safer and easier to use in real hospitals.

---

## 1. Introduction

Finding cancer as early as possible is the most effective way to save lives. When we catch the disease in its first stages, doctors can start treatment before it spreads, which leads to much better outcomes for families and patients. For many years, the most important tool in a doctor's kit has been the blood test. These tests look for "biomarkers"—simple signals in our blood, like specific proteins, that might go up when something is wrong in the body. For example, a high level of a protein called PSA might suggest a problem with the prostate, while AFP might point to issues in the liver. However, these signals are rarely perfect. Every person’s body is a little bit different, and what looks like a high number for one patient might be perfectly normal for another. This variability makes it very difficult to make a diagnosis based on just one or two numbers.

The history of biomarker testing shows us how far we have come, but also highlights the new challenges we face. Decades ago, testing was a slow and manual process where a lab technician would count cells under a microscope. Today, we have amazing machines that can measure hundreds of different biomarkers from just a single drop of blood. This sounds like a dream come true for medicine, but it has actually created a "data explosion." Doctors today are often overwhelmed by the sheer volume of information they receive. Instead of looking at a few lines on a piece of paper, they are now looking at massive digital spreadsheets filled with thousands of data points. The human brain, as wonderful as it is, was not designed to keep track of fifty different variables at once and see how they all interact in a complex web of risk.

Because of this data explosion, a serious "information gap" has formed in our hospitals. We have all the data we need to find cancer earlier than ever, but we are missing the tools that can put those clues together in a way that makes sense. For a long time, we tried to solve this with simple "cutoff rules." A doctor might say, "If your score is over 4.0, we will do a biopsy." But these rules are often too rigid. They miss patients who have a score of 3.8 but are showing a dangerous upward trend, and they might accidentally flag healthy patients who naturally have a score of 4.2. Cancer is subtle and smart; it doesn't always follow a single rule. It creates a pattern across many different markers, and if we only look at one marker at a time, we stay blind to the bigger picture.

To help close this gap, the world of medicine has turned to Artificial Intelligence, or AI. AI programs are incredibly good at finding patterns in huge amounts of data that humans would never notice. They can look at a thousand patients at once and learn exactly what a "high-risk" pattern looks like. However, these programs have a major problem that has stopped them from being used in every clinic: they are "Black Boxes." A Black Box is a program that gives you an answer but refuses to tell you how it got there. In a high-stakes environment like a hospital, this is a dangerous problem. A doctor cannot recommend a life-changing surgery or a toxic treatment just because a computer said so. They have to understand the logic behind the decision so they can explain it to the patient and be sure they are doing the right thing.

This lack of transparency has created a "Trust Gap" between technology and doctors. Many medical professionals feel that AI is like a "magic box"—it might be right most of the time, but if it is wrong, nobody knows why. This fear of the unknown is perfectly reasonable. In medicine, people's lives are on the line, and "magic" is not a substitute for clinical reasoning. We need AI that doesn't just act like a god telling us what to do, but acts like a partner that walks us through its thinking. We need to turn the "math" of the computer back into the "meaning" of the doctor. This means moving away from single mystery scores and toward systems that can explain their own red flags in plain language.

Our research proposes a new way forward by creating a "Clinical Dashboard" that treats AI like a "Committee of Experts." Instead of relying on just one secret algorithm, we use six different AI programs that work together. Think of it like a group of six specialized doctors sitting around a table, each looking at the patient's data from a slightly different perspective. One might focus on long-term trends, while another focuses on sudden spikes in the data. When they all agree, the doctor can be very confident in the results. If they disagree, the system flags the patient for a "Manual Review," which keeps the human doctor in control of the final decision. This "teamwork" approach significantly reduces the chance of a single program making a mistake and builds a much stronger foundation of trust.

Furthermore, we use a special kind of mapping tool called a "Graph Neural Network." You can think of this as a "Digital Map" of a patient's health. In most older computer tools, each biomarker is treated like an island—completely alone. In our system, the computer learns how the biomarkers are "talkers" that communicate with each other. For example, if Marker A usually stays low when Marker B is high, the computer learns this relationship as a healthy baseline. If it suddenly sees Marker A and Marker B both spiking together, it recognizes that the "dialogue" between these biomarkers has changed. This relational way of thinking allows the computer to spot cancer signals much earlier, much like an experienced doctor who has seen thousands of patients and knows when a pattern "feels" wrong.

Finally, we believe that a good tool should not just find a problem, but help solve it. Our dashboard includes a feature called "What-If" planning. When the computer finds a high risk, it doesn't just say "danger." It provides a clear target for treatment. It might say, "The patient's risk is currently 80%, but if we can reduce this specific biomarker by 25%, the risk will drop to a safe level." This gives the doctor a tangible goal to aim for and helps the patient understand exactly what is happening in their body. It turns a scary diagnosis into a clear plan of action. Our mission with this study is to show that when AI is transparent, collaborative, and easy to understand, it becomes the most powerful weapon we have in the fight against cancer. By making the computer's logic as clear as a doctor's intuition, we can find cancer sooner, save more lives, and move toward a future where technology and humanity work perfectly together.

---

## 2. Materials and Methods

### 2.1 The Clinical Patient Cohort
To build and test our system, we used a dataset of 1,000 patient records. Each record contained results from multiple blood tests, including markers like PSA, AFP, and CA125. This group was carefully selected to include both healthy people and patients with different types of malignancy. This variety is important because it teaches the computer to recognize a wide range of biological "signatures" rather than just looking at one specific type of case.

### 2.2 Data Cleaning and Preparation
Before the AI committee can analyze the data, it must be "cleaned" to remove errors. We used a method that standardizes all the numbers so they are on the same scale. One important step we took was to protect the "peaks" in the data. In most computer programs, unusually high numbers are seen as mistakes and are deleted. But in cancer testing, a high number is often the most important signal! We used a method that keeps these "spikes" while smoothing out small, unimportant errors. This ensures that the AI stays focused on the real signs of sickness.

### 2.3 The "Digital Map" (Relational Mapping)
A core part of our system is how it maps the connections between different health markers. Most older programs look at markers as if they were symbols standing alone. Our system uses a "Graph Neural Network," which we call a Digital Map. It creates a network showing which markers usually go up together. For example, if Marker A usually increases when Marker B does, the computer learns this relationship. If it sees Marker A go up *without* Marker B, it realizes something is unusual. This relational thinking is very similar to how an expert doctor uses their experience to spot odd patterns.

### 2.4 The Committee of Experts (Ensemble)
Instead of relying on a single computer program, we used an "Ensemble" of six different AI models. Each model uses a different mathematical approach to analyze the data—some look at broad trends, while others look at tiny details.
1.  **Agreement Voting**: All six models must "vote" on a case.
2.  **Risk Consensus**: We calculate a "Consensus Score" based on how many models agree.
3.  **Grey Zone Detection**: If the models disagree (for example, 3 say yes and 3 say no), the system flags the patient for a "manual review" by a human specialist. This prevents the computer from making a guess when it is unsure.

### 2.5 What-If Scenarios and Explainability
When the system identifies a risk, it provides the doctor with a "Reasoning Report." This report uses a feature called SHAP to show exactly which marker contributed most to the risk. Furthermore, we implemented "What-If" scenarios. The computer can simulate what would happen if a patient's biomarker levels improved. For example, it might show: *"If this marker drops by 30%, the overall cancer risk returns to a safe level."* This gives the doctor a tangible target for treatment and helps the patient understand the goals of their care.

---

## 3. Results and Discussion

Our testing showed that the "Committee" approach is much more accurate than using just one program. By combining the results of multiple models, we were able to find more early-stage cases while also reducing the number of "false alarms." The Relational Mapping tool was particularly helpful in identifying atypical cases that didn't follow the standard high-cutoff rules.

Clinicians who used the dashboard reported that the "What-If" scenarios were the most valuable part of the system. It allowed them to quickly see which biomarkers were the "driving force" behind a patient's risk. This transparency made them feel much more comfortable using the AI's advice. The system also proved to be very fast, processing large cohorts of patients in seconds, making it practical for a busy hospital environment.

---

## 4. Conclusion

This study proves that AI can be a powerful and transparent ally in the field of oncology. By moving away from "Black-Box" machines and toward an "Expert Committee" that explains its reasoning, we can build a system that doctors truly trust. Our approach of connecting biomarkers through digital mapping and providing clear "What-If" goals makes the path from testing to treatment much clearer. We believe this system is a major step toward a future where every patient gets the benefit of a team of AI experts working alongside their doctor to find and fight cancer as early as possible.
