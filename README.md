# RAGBOT

Generic RAG Application with Databases Integrations and LLM-Guided Evaluations.

## Design Description

In this demonestration, we used the _models-controllers-views_ software design pattern such that any interation with the databases is the `models`' responsibility what accepts inputs and return outputs that adhere to a specific _database schema_. The `controllers` are the intermediate layers bewteen the `views` (User interface or Front End) and the `models` such that any processing needed of the user inputs to be passed to models is made by the `controllers`. The RESTful API `endpoints` / `routes` can also be considered part of the `controllers`.

What you should see in the `src` directory should reflect these concepts as follows.

```terminal
src
├── assets
├── configs
├── controllers
├── helpers
├── locales
├── main.py
├── models
├── requirements.txt
└── routes
```

- `assets`: contains any resources and temp files needed for the porject.
- `configs`: contains all the configurations (text mappings) needed by all modules.
- `controllers`: contains all the controllers.
- `helpers`: contains the project settings (currently saved in the `.env` file. different from `configs`) and all future `utils`.
- `locales`: contains all the _prompt templates_ for the different types of _Generative AI_ behaviors (Agentic AI and such).
- `models`: contains all the models.
- `routes`: contains all the `endpoints` (info endpoints are still under development).
- `main.py`: combines all the routes connect them to the `FastAPI` _app_. You can disconnect whatever you want any time from this file.

## Setup

### Quick Setup

```terminal
.
├── Dockerfile
├── LICENSE
├── README.md
├── docker-compose.yml
├── src
├── weave-ops-with-latency.png
├── weave-ops.png
├── weave-sample-op-response.png
└── weave-sample-op.png
```

The code is relatively straight forward to start with. You only need `docker` engine and `git` installed to start working.

As you can see from directories above, the backend code in `src` has a `Dockerfile` that builds its image. The same is also applied for the _frontend_ code in `app` but it hasn't been added yet. All other servies that is needed for the application to run along with the `backend` code are implemented in the `docker-compose.yml` file.

To start working, implement the following steps sequentially.

- Clone the _GitHub_ repository and navigate inside its directory.

  ```bash
  git clone https://github.com/e-hossam96/AI-Powered-QA-System-for-ASAP_Systems.git application
  cd application
  ```

- Fill the `.env.example` fill and save it into `.env` in the same directory. This wil hold the setups and secret keys to run the application.

  ```bash
  cp .env.example .env
  ```

- Start the servies in the `docker-compose.yml` file.

  ```bash
  docker compose -p application -f docker-compose.yml up --build
  ```

You are now up and running and can start calling the endpoints using `curl` (description below).

### Development Setup

At any point if you would like to update the codes and test them, you can create the needed `conda` environment as follows.

- Install developer tools for C++ package building.

  ```bash
  sudo apt update
  sudo apt upgrade -y
  sudo apt install build-essential
  ```

- Download and install `miniconda`.

  ```bash
  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
  bash Miniconda3-latest-Linux-x86_64.sh -b -p ./miniconda
  ```

- Activate conda `base` environment.

  ```bash
  source ./miniconda/bin/activate
  ```

- Create the **ragbot** environment.

  ```bash
  conda create -n ragbot python=3.11.9
  ```

- Intall the `pip` dependencies.

  ```bash
  cd src
  python -m pip install -r requirements.txt
  ```

- `OR` you can directly create the environment and install the dependencies using the conda `environment.yml` file.

  ```bash
  conda env create
  ```

And now you can start developing the codes. Notice, that the `docker` services (except the backend image) and the `.env` file are still needed for development .

## API Endpoints

We have implemented 7 `endpoints` that you can use. Only one of them, the `rag-query`, should be exposed to the public. The rest are for the application setup. Aside from the `base` and the `push/asset` endpoints, each endpoint have a _query schema_ tha can be found in the `route_schemas` under the `routes` directory. The endpoints' short descriptions and call examples are as follows.

- Base

  To be used for health checks to see if the pllication is up.

  ```bash
  curl -X GET http://localhost:8000
  ```

- Asset Push

  To be used to push an asset file (`PDF` or `Plain Text`) to the database. Upon calling it, the file will be recieved and saved locally while information about its localion are saved in a _MongoDB_ collection called `assets`.

  ```bash
  curl -X POST http://localhost:8000/data/push/asset \
   -F "asset=@/path/to/your/file"
  ```

- Asset Process

  To be used to process either an asset using its `name` in the database or _all_ the assets that can be found in the `assets` collection. This will only split the texts into meaningful chunks using `LangChain`'s `RecursiveCharacterTextSplitter` based on the settings you defined in the `.env` file, see [.env.example](.env.example) file for reference, and saves the chunks into a collection called `chunks`.

  If you have a _MonogDB_ with the collection name `assets`, you provide its connection in the `.env` file and process all it chunks directly.

  ```bash
  curl -X POST http://localhost:8000/data/process/asset \
     -H "Content-Type: application/json" \
     -d '{
          "chunk_size": 2000,
          "overlap_size": 100,
          "do_reset": true
         }'

  ```

- Webpage Process

  To be used to process texts from `webpages`, same as the endpoint above, and saved the chunks into the `assets` collection. Notice, special API was used to collect texts from _Wikipedia_ pages to adhere with their guidlines.

  ```bash
  curl -X POST http://localhost:8000/data/process/webpage \
     -H "Content-Type: application/json" \
     -d '{
          "asset_name_or_url": "https://en.wikipedia.org/wiki/Roman_Empire",
          "chunk_size": 2000,
          "overlap_size": 100,
          "do_reset": false
         }'

  ```

- Index Push

  To be used to push the vectorized chunks into the `Qdrant` **Vector Database** after embedding them using the `AsyncOpenAI` client. Note that we use **OpenAI's Python SDK** to call different LLMs (for embeddings and text generations) by changing the `base_url` parameter. This setting is also added in the `.env` file.

  ```bash
  curl -X POST http://localhost:8000/index/push \
     -H "Content-Type: application/json" \
     -d '{
          "do_reset": true
         }'
  ```

- Index Search

  To be used to query vector database.

  ```bash
  curl -X POST http://localhost:8000/index/search \
     -H "Content-Type: application/json" \
     -d '{
          "text": "How long did the roman empire rule?",
          "limit": 4
         }'
  ```

- RAG Query (_main endpoint_)

  To be used to send queries to the backend LLM and get a response back. Notice that this endpoint also accepts a `chat_history` parameter to continue the converation along with the _user query_. Currently, the endpoint takes only the _raw_ user query and use it to seach the vector database. The chat history is added for the LLM's reference for now. Later on, the LLM can be provided with the _index search_ tool that it can call using the _adapted_ user query (adapted based on the chat history). ~`I might add this functionality today!`~ **`Added`**

  ```bash
  curl -X POST http://localhost:8000/rag/query \
     -H "Content-Type: application/json" \
     -d '{
          "text": "How long did the roman empire rule?",
          "limit": 4
         }'
  ```

- Evaluation

  To be used to call the `weave` evaluations and log the results into the project's dashboard on `weave`.

  ```bash
  curl -X GET http://localhost:8000/rag/evaluate
  ```

  The _demo_ evaluation result logs we provide can be access using the following `cURL` call. _Ensure you have a WANDB_API_KEY set in your environment_.

  ```bash
  curl 'https://trace.wandb.ai/calls/stream_query' \
    -u api:$WANDB_API_KEY \
    -H 'content-type: application/json' \
    --data-raw '{
      "project_id":"e_hossam96/ragbot",
      "filter":{"op_names":["weave:///e_hossam96/ragbot/op/Evaluation.evaluate:*"],"trace_roots_only":false},
      "limit":10000,
      "offset":0,
      "sort_by":[{"field":"started_at","direction":"desc"}],
      "include_feedback": true
    }'
  ```

Feel free to used the _lastest_ postman collection provided here, [postman-collection](./src/assets/asap.postman_collection.json), to quickly set the calls up.

## LLMops

We have used **Weights & Biases**' `weave` to monitor the interactions with the backend LLMs (embedding and chat). Using `weave`, we can directly add feedbacks to the LLMs calls using _thumbs-up_ 👍 and _thumbs-down_ 👎 emojis and notes. This helpful in case we needed to collect fine-tuning data to further inhance our application. User feedbacks can also be integrated using the same options with just slight modification to the frontend code and a dedicated endpoint to collect the feedbacks. We believe this can be easily added later.

The dashboard link of the application's project on **Weights & Biases** can accessed from [Dashboard](https://wandb.ai/e_hossam96/ragbot/weave).

## Notes

The following **Wikipedia** pages were used as our knowledge base.

- [World War II](https://en.wikipedia.org/wiki/World_War_II)
- [History of Artificial Intelligence](https://en.wikipedia.org/wiki/History_of_artificial_intelligence)
- [Ancient Egypt](https://en.wikipedia.org/wiki/Ancient_Egypt)
- [Roman Empire](https://en.wikipedia.org/wiki/Roman_Empire)

## License

MIT
