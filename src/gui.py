__version__ = "1.0.0"

import random
from typing import List

from dataclasses import dataclass
from typing import Optional


@dataclass
class QuestionModelOutput:
    question: str
    answer: Optional[str] = None
    positive_feedback: Optional[bool] = None

    @property
    def question_answered(self):
        return self.answer is not None

    def as_dict(self):
        return {
            "question": self.question,
            "answer": self.answer,
            "positive_feedback": self.positive_feedback
        }

    @classmethod
    def from_dict(cls, question, answer, positive_feedback):
        return QuestionModelOutput(question=question, answer=answer, positive_feedback=positive_feedback)


app_name = "contract2human-demo"

import streamlit as st

st.set_page_config(layout='wide', page_title=f'{app_name} {__version__}')
ss = st.session_state

import css
import prompts
import model
import storage
import feedback

QUESTIONS = [
    "Was sind die Arbeitszeiten?",
    "Gibt es Betriebsferien?",
    "GIbt es ein Formerfordernis der Kündigung?",
    "Gibt es Formerfordernisse von zusätzlichen Vereinbarungen?",
    "Gibt es eine Fortzahlung der Arbeitsvergütung im Krankheitsfall?",
    "Ist das Arbeitsverhältnis zeitlich begrenzt?",
    "Kündigungsfrist während der Probezeit?",
    "Sind Nebentätigkeit erlaubt?",
    "Welche Pflichten hat der Arbeitnehmer bei Arbeitsunfähigkeit?",
    "Welche Regelungen gibt es zur Urlaubsabwicklung während der Kündigung?",
    "Wie lange beträgt die Urlaubsdauer?",
    "Gibt es Regelungen zum Verfall des gesetzlichen Urlaubs?",
    "Gibt es Regelungen zum Verfall des Zusatzurlaubs?",
    "Gibt es Regelungen zum Verfall von Ansprüchen?",
    "Gibt es eine Verschwiegenheitspflicht?",
    "Wann beginnt das Arbeitsverhältnis?",
    "Was ist die Arbeitstätigkeit?",
    "Wie ist die Vergütung?",
    "Wie lange beträgt die Kündigungsfrist?",
    "Wie lange dauert die Probezeit?",
]

ANSWERS_OUTPUT: List[QuestionModelOutput] = [QuestionModelOutput(question=q) for q in QUESTIONS]


def set_answer_feedback(idx: int, positive: bool):
    st.write("Hinaaaaaaaaa")
    global ANSWERS_OUTPUT
    st.write(f"{idx} - {positive}")
    print(f"Length before: {ANSWERS_OUTPUT}")
    ANSWERS_OUTPUT[idx].positive_feedback = positive
    ss['questions'] = ANSWERS_OUTPUT
    print(f"Length after: {ANSWERS_OUTPUT}")
    st.experimental_rerun()
    # readd_questions()


st.write(f'<style>{css.v1}</style>', unsafe_allow_html=True)
header1 = st.empty()  # for errors / messages
header2 = st.empty()  # for errors / messages
header3 = st.empty()  # for errors / messages


def ui_spacer(n=2, line=False, next_n=0):
    for _ in range(n):
        st.write('')
    if line:
        st.tabs([' '])
    for _ in range(next_n):
        st.write('')


def ui_info():
    st.markdown(f"""
        # contract2human
        version {__version__}
    """)
    ui_spacer(1)


def load_api_key():
    api_key = "3oMx1QIkqaLyBrrrqUIaJFkblB3TvZiinFrgFXUuSk6zKDSM-ks"
    model.use_key(api_key[::-1])
    if 'data_dict' not in ss:
        ss['data_dict'] = {}
    ss['api_key'] = api_key
    ss['storage'] = storage.get_storage(api_key, data_dict=ss['data_dict'])
    ss['user'] = ss['storage'].folder
    model.set_user(ss['user'])
    ss['feedback'] = feedback.get_feedback_adapter(ss['user'])
    ss['feedback_score'] = ss['feedback'].get_score()


def index_pdf_file():
    if ss['pdf_file']:
        ss['filename'] = ss['pdf_file'].name
        index = model.index_file(ss['pdf_file'], fix_text=ss['fix_text'], frag_size=ss['frag_size'], pg=ss['pg_index'])
        ss['index'] = index
        debug_index()


def debug_index():
    index = ss['index']
    d = {}
    d['hash'] = index['hash']
    d['frag_size'] = index['frag_size']
    d['n_pages'] = len(index['pages'])
    d['n_texts'] = len(index['texts'])
    d['summary'] = index['summary']
    d['pages'] = index['pages']
    d['texts'] = index['texts']
    d['time'] = index.get('time', {})


def ui_pdf_file():
    st.write('## Upload your contract')
    ss['pg_index'] = st.progress(0)
    st.file_uploader(
        'pdf file', type='pdf', key='pdf_file', disabled=False, on_change=index_pdf_file,
        label_visibility="collapsed"
    )


def ui_fix_text():
    st.checkbox('fix common PDF problems', value=True, key='fix_text')


def ui_temperature():
    # st.slider('temperature', 0.0, 1.0, 0.0, 0.1, key='temperature', format='%0.1f')
    ss['temperature'] = 0.0


def ui_fragments():
    # st.number_input('fragment size', 0,2000,200, step=100, key='frag_size')
    st.selectbox('fragment size (characters)', [0, 200, 300, 400, 500, 600, 700, 800, 900, 1000], index=3,
                 key='frag_size')
    b_reindex()
    st.number_input('max fragments', 1, 10, 4, key='max_frags')
    st.number_input('fragments before', 0, 3, 1, key='n_frag_before')  # TODO: pass to model
    st.number_input('fragments after', 0, 3, 1, key='n_frag_after')  # TODO: pass to model


def ui_model():
    models = ['gpt-3.5-turbo', 'text-davinci-003', 'text-curie-001']
    st.selectbox('main model', models, key='model')
    st.selectbox('embedding model', ['text-embedding-ada-002'], key='model_embed')  # FOR FUTURE USE


def ui_hyde():
    st.checkbox('use HyDE', value=True, key='use_hyde')


def ui_hyde_summary():
    st.checkbox('use summary in HyDE', value=True, key='use_hyde_summary')


def ui_task_template():
    st.selectbox('task prompt template', prompts.TASK.keys(), key='task_name')


def ui_task():
    x = ss['task_name']
    st.text_area('task prompt', prompts.TASK[x], key='task')


def ui_hyde_prompt():
    st.text_area('HyDE prompt', prompts.HYDE, key='hyde_prompt')


def ui_question():
    st.write('## Ask contract questions' + f' for contract {ss["filename"]}' if ss.get('filename') else '')
    disabled = not ss.get('api_key')
    st.text_area('question', key='question', height=100, placeholder='Enter question here', help='',
                 label_visibility="collapsed", disabled=disabled)


def process_questions():
    disabled = not ss.get('api_key') or not ss.get('index')
    if st.button('Generate Predefined Answers', disabled=disabled, type='primary', use_container_width=True):
        temperature = ss.get('temperature', 0.0)
        hyde = ss.get('use_hyde')
        hyde_prompt = ss.get('hyde_prompt')
        if ss.get('use_hyde_summary'):
            summary = ss['index']['summary']
            hyde_prompt += f" Context: {summary}\n\n"
        task = ss.get('task')
        max_frags = ss.get('max_frags', 1)
        n_before = ss.get('n_frag_before', 0)
        n_after = ss.get('n_frag_after', 0)
        index = ss.get('index', {})

        ss['output'] = ''
        with st.spinner('Preparing the contract2human answers...'):
            for idx, question in enumerate(QUESTIONS):
                resp = model.query(
                    question,
                    index,
                    task=task,
                    temperature=temperature,
                    hyde=hyde,
                    hyde_prompt=hyde_prompt,
                    max_frags=max_frags,
                    limit=max_frags + 2,
                    n_before=n_before,
                    n_after=n_after,
                    model=ss['model'],
                )

                q = question.strip()
                a = resp['text'].strip()

                st.markdown("""<hr style="height:6px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns([2, 3, 1, 1])
                c1.markdown(q)
                c2.markdown(a)
                if c3.button('👍', use_container_width=True, disabled=False, key=f"positive_feedback{idx}-{random.randint(0, 1000000000)}"):
                    set_answer_feedback(idx=idx, positive=True)
                if c4.button('👎', use_container_width=True, disabled=False, key=f"negative_feedback{idx}-{random.randint(0, 1000000000)}"):
                    set_answer_feedback(idx=idx, positive=False)


def b_clear():
    if st.button('clear output'):
        ss['output'] = ''


def b_reindex():
    if st.button('reindex'):
        index_pdf_file()


def b_reload():
    if st.button('reload prompts'):
        import importlib
        importlib.reload(prompts)


def b_delete():
    db = ss.get('storage')
    name = ss.get('selected_file')
    # TODO: confirm delete
    if st.button('delete from ask-my-pdf', disabled=not db or not name):
        with st.spinner('deleting from ask-my-pdf'):
            db.delete(name)
        st.experimental_rerun()

#
# def readd_questions():
#     global QUESTIONS_DIV
#     QUESTIONS_DIV.empty()
#
#     QUESTIONS_DIV = st.container()
#     QUESTIONS_DIV.markdown(f'Feedback: {[q.positive_feedback for q in ss.get("questions", [])]}')
#
#     for idx, question in enumerate(ss.get('questions', [])):
#         QUESTIONS_DIV.markdown("""<hr style="height:6px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
#         c1, c2, c3, c4 = QUESTIONS_DIV.columns([2, 3, 1, 1])
#         c1.markdown(question.question)
#         c2.markdown(question.answer)
#         if c3.button('👍', use_container_width=True, disabled=False, key=f"positive_feedback{idx}-{random.randint(0, 1000000000)}"):
#             set_answer_feedback(idx=idx, positive=True)
#         if c4.button('👎', use_container_width=True, disabled=False, key=f"negative_feedback{idx}-{random.randint(0, 1000000000)}"):
#             set_answer_feedback(idx=idx, positive=False)
#
#         # st.markdown("""<hr style="height:6px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
#         # c1, c2, c3, c4 = st.columns([2, 3, 1, 1])
#         # c1.markdown(question.question)
#         # c2.markdown(question.answer)
#         # if c3.button('👍', use_container_width=True, disabled=False, key=f"positive_feedback{idx}"):
#         #     set_answer_feedback(index=idx, positive=True)
#         # if c4.button('👎', use_container_width=True, disabled=False, key=f"negative_feedback{idx}"):
#         #     set_answer_feedback(index=idx, positive=False)
#
#     if QUESTIONS_DIV.button('SUBMIT FEEDBACK', disabled=False, type='primary', use_container_width=True):
#         import json
#
#         # Create a dictionary
#         data = {
#             "name": "John",
#             "age": 30,
#             "city": "New York"
#         }
#
#         # Open a file for writing and write the dictionary to the file as JSON
#         with open("data.json", "w") as file:
#             json.dump([a.as_dict() for a in ss.get("questions", [])], file)


with st.sidebar:
    ui_info()
    ui_spacer(2)
    with st.expander('advanced'):
        b_clear()
        ui_model()
        ui_fragments()
        ui_fix_text()
        ui_hyde()
        ui_hyde_summary()
        ui_temperature()
        b_reload()
        ui_task_template()
        ui_task()
        ui_hyde_prompt()

load_api_key()
ui_pdf_file()
process_questions()


