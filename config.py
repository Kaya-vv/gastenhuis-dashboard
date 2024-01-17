KEY = "ck_c4be3812ec89cb3c9c8d367694e82baab50731b6"
SECRET = "cs_03411475636aab1bf1efed4af913284d225a3d10"
base_url = 'https://hetgastenhuis.nl/wp-json/gf/v2'
forms = {
    "Brochure wonen": 5,
    "Brochure werken": 43,
    "Klantaanmeldingen": 2
}


infobijeenkomst_form = {}


form_name = list(forms.keys())

form_field_id = {
    "Brochure wonen": 1,
    "Brochure werken": 16,
    "Klantaanmeldingen": 4
}