import langchain
import transformers
from DocLoader import docload
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_huggingface.llms import HuggingFacePipeline
import langchain_core
import langchain_text_splitters
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders import DirectoryLoader, TextLoader, JSONLoader
from langchain.agents import AgentType
from langchain.memory import ConversationEntityMemory
import faiss
from langchain_community.docstore import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from RAG_VectorDB import vectordb
from DocLoader import docload
from langchain.memory.prompt import ENTITY_MEMORY_CONVERSATION_TEMPLATE
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from operator import itemgetter




class chat_chain():
    def __init__(self, llm, memory, retriever):
        self.llm = llm
        self.memory = memory
        self.retriever = retriever

    def get_chain_ordinary(self, prom):
        prompt = ENTITY_MEMORY_CONVERSATION_TEMPLATE + prom
        o_chain = prompt | self.llm | StrOutputParser()
        return o_chain
    
    def get_chain_account(self, data_path):
        prompt = PromptTemplate(
        input_variables=["chat_history", "query"],

            template=f"""
            당신은 가계부 데이터를 포함한 파일({data_path})에 접근할 수 있는 보조 AI입니다.
            당신은 무조건 한글로만 답해야 합니다
            금액의 단위는 원입니다

            이 데이터를 사용하여 다음 질문에 답변해 주세요:

            {{query}}
            예시)
            input : 카페에 총 얼마 썼는지 알려줘
            AI : 카페에 총 n원을 썼습니다
            """
        )

        ac_chain = LLMChain( prompt = prompt, llm = self.llm, memory = self.memory)
        return ac_chain
    
    def get_chain_recsys(self):
        prompt = ChatPromptTemplate.from_template([
            ("system", "소비내역과 카드 정보, 카드 추천 시스템을 바탕으로 혜택이 큰 카드를 추천해줍니다"),
            ("user", "{user_input}")
        ])
        rec_chain = prompt | self.llm | StrOutputParser()
        return rec_chain
    
    def chat_rec(self, input):
        rec_chat = self.get_chain_recsys()
        recommendation = self.rec_model(input)
        out = rec_chat.invoke({"user" : input, "recommendations" : recommendation})
        return out
    
    def save_memory(self, input, output):
        context = self.memory.save_context({"input" : input},{"output" : output})
        return context