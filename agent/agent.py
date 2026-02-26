import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from agent.tools import get_donnees_projet, outil_dimensionnement, outil_rentabilite

load_dotenv()

def creer_agent():
    """Crée et retourne l'agent LangGraph configuré avec Groq"""

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.1
    )

    outils = [get_donnees_projet, outil_dimensionnement, outil_rentabilite]

    system_prompt = """Tu es un expert en dimensionnement de systèmes photovoltaïques off-grid.

Ton rôle est d'analyser les données fournies et de produire un dimensionnement précis et professionnel.

Voici comment tu dois procéder :
1. Commence par appeler get_donnees_projet pour récupérer toutes les données disponibles
2. Analyse les composants disponibles fournis par l'utilisateur
3. Si l'utilisateur a des panneaux, utilise leur puissance. Sinon propose 400Wc par défaut
4. Si l'utilisateur a des batteries, utilise leur tension. Sinon propose 24V par défaut
5. Appelle outil_dimensionnement avec les bons paramètres
6. Appelle outil_rentabilite avec la puissance installée obtenue
7. Rédige un rapport structuré en français avec :
   - Le résumé de la consommation analysée
   - Le dimensionnement recommandé (panneaux, batterie, onduleur)
   - Le tableau comparatif pour différentes puissances de panneaux
   - L'étude de rentabilité
   - Des recommandations professionnelles

Sois précis, professionnel et pédagogique dans tes explications.
Utilise toujours les unités correctes (Wc, kWc, Ah, kWh, V)."""

    agent = create_agent(
        model=llm,
        tools=outils,
        system_prompt=system_prompt
    )

    return agent


def lancer_analyse(message_utilisateur: str) -> str:
    """
    Lance l'agent avec le message de l'utilisateur
    et retourne la réponse complète
    """
    agent = creer_agent()

    resultat = agent.invoke({
        "messages": [HumanMessage(content=message_utilisateur)]})

    return resultat["messages"][-1].content