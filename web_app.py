import re
import requests
import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(layout='wide')

BASE_URL = 'http://127.0.0.1:8000'


def get_scores(url: str):
    return requests.get(f'{BASE_URL}/process/?url={url}')#, json={'url': url})

def is_youtube_url(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return re.match(youtube_regex, url) is not None

def scores_to_dfs(scores: dict) -> (pd.DataFrame, pd.DataFrame):
    audio_df = []
    scores['audio_score'] = scores['audio_score'][0]
    for category in scores['audio_score'].keys():
        if scores['audio_score'][category]['valid']:
            audio_df.append((category, scores['audio_score'][category]['confidence']))
    audio_df = (pd.DataFrame(data=audio_df, columns=['category', 'confidence'])
                .sort_values(by='confidence', ascending=False))

    frame_dfs = []
    for i, frame in enumerate(scores['frames_score']):
        _frame = []
        for category in frame.keys():
            if frame[category]['valid']:
                _frame.append((category, frame[category]['confidence']))
        frame_dfs.append(pd.DataFrame(data=_frame, columns=['category', 'confidence'])
                         .sort_values(by='confidence', ascending=False))
        scores['frames_score'][i]['df'] = frame_dfs[-1]

    _visual_df = pd.concat(frame_dfs)
    visual_df = []
    for category in _visual_df['category'].unique():
        visual_df.append((category, _visual_df[_visual_df['category'] == category]['confidence'].max()))
    visual_df = (pd.DataFrame(data=visual_df, columns=['category', 'confidence'])
                .sort_values(by='confidence', ascending=False))
    return visual_df, audio_df

def app():
    def clear_url(key='youtube_url_input'):
        st.session_state[key] = ''

    response = None

    with st.sidebar:
        st.title(':orange[**ZeitGeist**]')
        # st.markdown("<h1 style='text-align: center; color: orange;'>ZeitGeist</h1>", unsafe_allow_html=True)
        st.header(':orange[Introducing our video classification pipeline]')
        st.divider()
        # st.markdown('Please select a **[:red[YouTube]](https://youtube.com)** video that is no more than 4 minutes long.')
        st.markdown('Please select a **[YouTube](https://youtube.com)** video that is no more than 4 minutes long.')
        youtube_url = st.text_input('Place YouTube url here:', '', key='youtube_url_input', placeholder='')

        c1, c2 = st.columns(2, gap="small", vertical_alignment="top", border=False)
        with c1:
            if st.button('Process', disabled=not is_youtube_url(youtube_url), key='process_button'):
                with st.spinner('Please wait...'):
                    response = get_scores(youtube_url)
        with c2:
            st.button('Clear', key='clear_button', on_click=clear_url,
                      disabled=len(st.session_state['youtube_url_input']) == 0)#, disabled=not is_youtube_url(youtube_url))

        if response is not None:
            if response.status_code == 200:
                st.success('Successful processing.')
            else:
                st.error(f'Error: {response.json().get("detail")}')

    if response is not None:
        scores = response.json()
        # st.json(scores)
        st.video(youtube_url if youtube_url.startswith('https://') else 'https://' + youtube_url)
        visual_df, audio_df = scores_to_dfs(scores)

        col1, col2 = st.columns(2, gap="medium", vertical_alignment="top", border=True)

        # visual
        with col1:
            st.header('Visual')
            if len(visual_df) == 0:
                st.success('neutral')
            else:
                st.error('detected categories')
                st.dataframe(visual_df, use_container_width=True, hide_index=True)

            st.divider()

            with st.expander('Frames Breakdown'):
                # for im, frames_score in zip(scores['key_frames'], scores['frames_score']):
                for frames_score in scores['frames_score']:
                    df = frames_score['df']
                    if len(df) == 0:
                        st.success('neutral')
                    else:
                        st.error('detected categories')
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    # st.image(np.array(im, dtype='uint8'))

                    st.divider()

        # audio
        with col2:
            st.header('Audio')
            if len(audio_df) == 0:
                st.success('neutral')
            else:
                st.error('detected categories')
                st.dataframe(audio_df, use_container_width=True, hide_index=True)

            st.divider()



app()

if __name__ == '__main__':
    # uploaded_file = '/home/ndor/Desktop/pipeline/video_samples/Who are the Palestinian Islamic Jihad militants and what do they want.mp4'
    # scores = video_pipe.process_video(uploaded_file)
    # visual_df, audio_df = scores_to_dfs(scores)
    # print(visual_df)
    # print('-'*99)
    # print(audio_df)
    pass
