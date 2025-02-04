from fire import Fire
from tqdm import tqdm

from training_dataset.create_test_case_and_prompt import \
    create_test_cases_using_gpt
from training_dataset.util import parse_incomplete_json
from utility.utility import append_jsonl, chunking, load_jsonl

MAX_CHUNK_SIZE = 50


def generate_evol_test_case(ct: int = 50):
    """step 2 of the process, generate test cases using chat gpt"""
    # we check for last generated responses, so we do not waste openAI tokens
    jsonl_file_name = "training_dataset/evol/data/evol_v2.jsonl"
    start_idx = 0
    try:
        past_data = load_jsonl(jsonl_file_name)
        last_idx = past_data[-1]["id"]
        start_idx = last_idx + 1
    except:
        # we start at 0 as we never inferenced before
        pass

    if start_idx >= ct and ct > 0:
        return  # we already finished inferencing

    # preparing the input
    data = load_jsonl("training_dataset/evol/data/evol_v1.jsonl")
    if ct > 0:
        data = data[:ct]
    data = data[start_idx:]
    data_chunks = chunking(data, MAX_CHUNK_SIZE)
    inferenced_ct = 0
    for chunk in tqdm(data_chunks):
        programs = [i["program"] for i in chunk]
        instructions = [i["instruction"] for i in chunk]
        responses = create_test_cases_using_gpt(
            programs=programs,
            instructions=instructions,
            use_cache=False,
            gpt4=True,
        )
        tests = []
        questions = []
        for i in responses:
            obj = parse_incomplete_json(i)
            question = obj.get("question", "please ignore this question")
            test = obj.get("tests", ["assert False"])
            questions.append(question)
            tests.append(test)
        for i in range(len(tests)):
            chunk[i]["tests"] = tests[i]
            chunk[i]["gpt_question"] = questions[i]

        append_jsonl(jsonl_file_name, chunk)
        inferenced_ct += len(chunk)
        print(f"openai finished generating test cases for {inferenced_ct} items")


if __name__ == "__main__":
    Fire(generate_evol_test_case)
