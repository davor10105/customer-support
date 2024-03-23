import streamlit as st
from audio_recorder_streamlit import audio_recorder
from openai import OpenAI
import streamlit as st


def response_generator(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        stream=True,
    )
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content


def generate_corrected_transcript(text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": """Ti si AI pomoćnik za servisera guma Vulkal. Tvoj zadatak je ispraviti greške u transkripciji govora korisnikovog upita na hrvatskom jeziku.
                Nemoj izmjenjivati značenje originalnog upita, samo promijeni greške.
                Upiti mogu biti na različitim hrvatskim dijalektima: štokavski, kajkavski i čakavski.""",
            },
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content


api_key = st.text_input("API key")
api_key_present = not (api_key is None or api_key == "")
print("api_key", api_key_present)
if api_key:
    client = OpenAI(api_key=api_key)
    st.divider()
    st.image("vulkal.webp")
    messages = st.container()
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "system",
                "content": """Ti si AI pomoćnik koji radi u customer supportu auto servisa Vulkal i govori hrvatski jezik. Budi ljubazan i odgovori na upite korisnika iskreno.
                Kada odgovaraš na pitanje, prvo klasificiraj korisnikovo pitanje u jednu od tri kategorije:
                    1. Savjet oko odabira guma
                    2. Provjera cijene usluga
                    3. Pravila dostave guma
                    4. Načini plaćanja u webshopu
                    5. Radno vrijeme poslovnica
                    6. Rezervacija termina servisa
                Uvijek svoj odgovor formatiraj na sljedeći način:
                [klasa pitanja]: [tvoj odgovor na pitanje]
                
                Primjer:
                Korisnik: Kada mogu rezervirati termin za promjenu guma?
                Pomoćnik: Rezervacija termina: [tvoj odgovor]
            """,
            }
        ]

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        if len(st.session_state.messages) == 1:
            with messages.chat_message("assistant"):
                st.markdown("Kako Vam mogu pomoći?")
        if message["role"] == "system":
            continue
        with messages.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    st.divider()
    audio_bytes = audio_recorder(
        text="Kliknite za snimanje",
        # recording_color="#e8b62c",
        neutral_color="#6aa36f",
        icon_size="1x",
    )
    if audio_bytes:
        # st.audio(audio_bytes, format="audio/wav")
        with open("output.wav", mode="bw") as f:
            f.write(audio_bytes)
            f.close()
        try:
            with open("output.wav", "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="hr",
                    temperature=0,
                )

            print(transcription.text)
            text = generate_corrected_transcript(transcription.text)
            # text = transcription.text

            with messages.chat_message("user"):
                st.markdown(text)
                st.session_state.messages.append({"role": "user", "content": text})
        except:
            pass

    # Display assistant response in chat message container
    if st.session_state.messages[-1]["role"] == "user":
        with messages.chat_message("assistant"):
            response = st.write_stream(response_generator(st.session_state.messages))
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
else:
    st.info("Unesite svoj API key za početak")
