import streamlit as st

st.title('Deploy App')
st.write('My First Deploy App !')

import os
key = os.environ.get('MY_SECRET', 'NOT SET YET')
st.write(f'Server key : {Key}')