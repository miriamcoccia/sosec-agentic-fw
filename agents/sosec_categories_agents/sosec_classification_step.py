import multiprocessing
from sosec_orchestrator_agent import SOSECOrchestratorAgent
from general_concerns_agent import GeneralConcernsAgent
from political_parties_agent import PoliticalPartiesAgent
from trust_institutions_agent import TrustInstitutionsAgent
from views_germany_usa_agent import ViewGermanyUsaAgent
from conspiracy_theories_agent import ConspiracyTheoriesAgent

def main():
    model = "llama3.2:latest"
    agents = [
        GeneralConcernsAgent(model),
        PoliticalPartiesAgent(model),
        TrustInstitutionsAgent(model),
        ViewGermanyUsaAgent(model),
        ConspiracyTheoriesAgent(model),
    ]
    orchestrator = SOSECOrchestratorAgent(
        agents,
        r"../../data/start_data_isr.csv",
        r"../../data/combined_results.csv"
    )
    orchestrator.run()

if __name__ == "__main__":
    multiprocessing.freeze_support()  
    multiprocessing.set_start_method("spawn", force=True)
    main()
