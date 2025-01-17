import streamlit as st
import os
key=os.environ.get('MY_SECRET','NOT SET YET')


st.title("TEST DEPLOY")

st.write(f'Server Key : {key}')