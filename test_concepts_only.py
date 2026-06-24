"""Quick test: just extract concepts from the ML pipeline lecture transcript."""
import os
os.environ.setdefault("LLM_ENABLED", "true")

from backend.core.utils.vtt_parser import parse_vtt, extract_concepts, llm_extract_concepts

# Read the VTT file if it exists, otherwise use a snippet
vtt_dir = None
for root, dirs, files in os.walk("outputs"):
    for f in files:
        if f.endswith(".vtt"):
            vtt_dir = os.path.join(root, f)
            break

# Try to find VTT in common locations
import glob
vtt_files = glob.glob("**/*.vtt", recursive=True)
print(f"Found VTT files: {vtt_files}")

if vtt_files:
    with open(vtt_files[0], "r") as f:
        vtt_text = f.read()
    print(f"\nUsing: {vtt_files[0]} ({len(vtt_text)} chars)")
else:
    print("No VTT files found, using embedded test snippet")
    # Use a representative snippet from the user's transcript
    vtt_text = """WEBVTT

1
00:12:07.730 --> 00:12:11.040
SUNIL SAUMYA: Okay, so we'll start now.

2
00:12:12.600 --> 00:12:20.280
SUNIL SAUMYA: So, the previous class, We started with,

3
00:12:20.700 --> 00:12:24.100
SUNIL SAUMYA: Because it was our first class, we started with the quick introduction to the machine learning, and we were trying to differentiate the machine learning with the conventional approach, okay?

4
00:12:34.210 --> 00:12:39.400
SUNIL SAUMYA: We have understood, essentially, two things, that in the machine learning. We machine learns from the data, the previous data, or experience, whatever you say, and while learning

5
00:12:47.800 --> 00:13:00.389
SUNIL SAUMYA: It tries to understand the pattern, and pattern here is being also shown by this term called as program, or somewhere it was shown by the term rules, or so on, right?

6
00:13:10.570 --> 00:13:22.419
SUNIL SAUMYA: So, machine learning is to make the computer learn from the data without being explicitly programmed. That is one thing. Other point of discussion in the previous class was that, okay, how it is different from the conventional approach and, like, the current machine learning approach.

7
00:25:03.440 --> 00:25:16.600
SUNIL SAUMYA: this task, where we have to predict whether a product review is positive or negative. Say that we are on the e-commerce websites, Flipkart, or Amazon, or any other website.

8
00:28:07.430 --> 00:28:11.129
SUNIL SAUMYA: may fail for the multiple context. Like, if someone is writing some reviews in the sarcasm manner, or someone is writing the mixed sentiment.

9
00:30:00.390 --> 00:30:01.619
SUNIL SAUMYA: vector vectorized data, TFIDF, embeddings, these are very popular now, but earlier in the conventional machine learning, these things were not popular, and people were using TFIDF, count vector, and so on.

10
00:34:48.020 --> 00:34:50.989
SUNIL SAUMYA: And there are a few more paradigms which we are going to cover.

11
00:35:02.030 --> 00:35:10.530
SUNIL SAUMYA: I had the problem statement, understood that the finally, the machine has to predict the review is positive or negative. That is the problem statement.

12
00:36:11.220 --> 00:36:20.699
SUNIL SAUMYA: So, first of all, when you have a data given for a given problem statement, you have to look out in the data whether I have input and output both are available in the data or not.

13
00:36:59.510 --> 00:37:13.910
SUNIL SAUMYA: So, given a problem statement, given a data, look out for even if the data has input-output both available, input-output information both available, supervised learning is the way to go.

14
00:38:18.680 --> 00:38:32.369
SUNIL SAUMYA: Unsupervised learning is the approach you will apply when this class information is not given. Problem statement is still same, input is still same, but say that class is not given in the data.

15
00:39:56.400 --> 00:40:11.990
SUNIL SAUMYA: Data is changing. If class label is available, it is a supervised. Class label is not available, unsupervised. If, suppose, none of these input, output, nothing is available, means you have to start from zero, ground to zero, okay?

16
00:40:11.990 --> 00:40:29.929
SUNIL SAUMYA: Then it there is something called as reinforcement, which you can apply. To understand this reinforcement learning idea, let us take some other example.

17
00:29:08.770 --> 00:29:18.160
SUNIL SAUMYA: One way is to do the feature extraction, okay? So I can extract some of the features, like noun, how many nouns are there in this sentence, how many pronouns are in this sentence.

18
00:29:18.160 --> 00:29:41.369
SUNIL SAUMYA: That is called parts of speech features, POS features, okay? There are libraries which support this extracting the POS feature from the given text. We can apply that directly and extract some of these features.

19
00:33:04.780 --> 00:33:19.960
SUNIL SAUMYA: Automatic features, automatic vectors, that is what we extract. Obviously, there is a logic behind it. We will understand as and when it is required, but for now, we just understand we convert each sentence here as a vector.

20
00:46:33.540 --> 00:46:49.609
SUNIL SAUMYA: So the rule of thumb is, if your data has input or output both, input label both, supervised learning is the way to go. You should not think any other kind of approach. Because label is always available, and for machine, when the output or label is available, that is the best way to learn.

21
00:21:55.410 --> 00:22:13.489
SUNIL SAUMYA: And hence, you need to identify some information from that English plain text, so that machine should understand. So here, noun-per-noun entropy, these are kind of a sum-some features. So that is what we have given a name as features, which we have extracted from the text, or sentences.

22
00:22:29.240 --> 00:22:41.010
SUNIL SAUMYA: these, these, words. So, features are nothing but it is a kind of transformation of your raw data. The raw data is in some other form. Now, you have transformed them into some other form.

23
00:49:46.850 --> 00:49:52.799
SUNIL SAUMYA: That, no, the food was not good. At least tomorrow morning, I'll not visit this hotel, I'll try some other hotel. This is reward and penalty in reinforcement learning.

24
00:50:06.680 --> 00:50:16.519
SUNIL SAUMYA: this, you can say that this, autonomous car. Autonomous car is a very good example for the reinforcement learning.
"""

# Parse
clean_text = parse_vtt(vtt_text)
print(f"\nClean transcript: {len(clean_text)} chars, {len(clean_text.split())} words")

# TF-IDF extraction (for comparison)
tfidf_concepts = extract_concepts(clean_text)
print(f"\nTF-IDF concepts: {tfidf_concepts}")

# LLM extraction (the real one)
llm_concepts = llm_extract_concepts(clean_text, tfidf_fallback_concepts=tfidf_concepts)
print(f"\nLLM-70B concepts: {llm_concepts}")
print(f"Count: {len(llm_concepts)}")

# Quality check
garbage_words = {"don", "doesn", "didn", "prediction", "statement", "understanding", 
                 "positive", "negative", "label", "features", "paradigms", "approach",
                 "method", "process", "concept", "example", "important", "difficult"}
found_garbage = [c for c in llm_concepts if c.lower() in garbage_words]
if found_garbage:
    print(f"\n❌ GARBAGE DETECTED: {found_garbage}")
else:
    print(f"\n✅ No garbage words detected!")
