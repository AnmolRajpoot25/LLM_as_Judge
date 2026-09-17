from gradio_client import Client


class HFJudgeClient:
    """
    Client for the fine-tuned Qwen2.5-7B
    deployed on Hugging Face ZeroGPU.
    """

    def __init__(self):
        self.client = Client("Anmol2507/LLM_as_Judge_API")

    def judge(
        self,
        problem: str,
        answer_a: str,
        answer_b: str
    ):
        """
        Send two candidate answers to the remote
        fine-tuned LLM judge.
        """

        result = self.client.predict(
            problem=problem,
            answer_a=answer_a,
            answer_b=answer_b,
            api_name="/judge"
        )

        return result
