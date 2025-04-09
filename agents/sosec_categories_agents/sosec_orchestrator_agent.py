import multiprocessing
import pandas as pd

def process_agent(agent, input_csv_path):
    """Standalone function for processing an agent."""
    print(f"Processing with {agent.__class__.__name__}...")
    temp_output_path = f"temp_{agent.__class__.__name__}.csv"
    agent.process_dataset(input_csv_path, temp_output_path, None)  # Added None for checkpoint_path
    result = pd.read_csv(temp_output_path)
    return result, agent.category_name

class SOSECOrchestratorAgent:
    def __init__(self, agents, input_csv_path, output_csv_path):
        self.agents = agents
        self.input_csv_path = input_csv_path
        self.output_csv_path = output_csv_path

    def run(self):
        data = pd.read_csv(self.input_csv_path, nrows=5)
        if 'Post Text' not in data.columns or 'date' not in data.columns:
            raise ValueError("Input CSV must contain 'Post Text' and 'date' columns.")

        results = {}
        with multiprocessing.Pool() as pool:
            # Use pool.apply_async to submit tasks
            future_to_agent = {pool.apply_async(process_agent, (agent, self.input_csv_path)): agent for agent in self.agents}
            for future in future_to_agent:
                agent = future_to_agent[future]
                try:
                    agent_result, agent_name = future.get()
                    results[agent_name] = agent_result
                except Exception as e:
                    print(f"Error processing {agent.__class__.__name__}: {e}")

        combined_results = data[['Post Text', 'date']].copy()
        for agent_name, agent_result in results.items():
            # Use the category_name from the agent as the column name
            category_col = agent_name  # This is now the category_name from the agent
            combined_results = pd.merge(
                combined_results,
                agent_result[['Post Text', category_col]],
                on='Post Text',
                how='left'
            )

        combined_results.to_csv(self.output_csv_path, index=False)
        print(f"Combined results saved to {self.output_csv_path}")

