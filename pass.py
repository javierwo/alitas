import streamlit_authenticator as stauth

hashed_passwords = stauth.Hasher(['sinche_a.23', 'sanchez_d.04', 'tenecora_t.15']).generate()
print(hashed_passwords)