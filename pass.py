import streamlit_authenticator as stauth

# asinche: sinche_a.23
# sanchezd: sanchez_d.04
# tenecorat: tenecora_t.15
# admin: admin.2024*
hashed_passwords = stauth.Hasher(['sinche_a.23', 'sanchez_d.04', 'tenecora_t.15', 'admin.2024*']).generate()
print(hashed_passwords)