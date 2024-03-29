from flask import jsonify, request, Blueprint, current_app
from flask_restful import Resource, Api
from datetime import datetime
from datetime import timedelta
import json
import os
from app.models import Observations
import logging
from flask_sqlalchemy import SQLAlchemy
from flask import current_app

logging.basicConfig(
    format="%(asctime)-15s [%(levelname)s] %(funcName)s: %(message)s",
    level=current_app.config["LOG_LEVEL"],
)

observations_blueprint = Blueprint("observations", __name__)
api = Api(observations_blueprint)

allowed_things = {
    "cesva": ["Noise-TA120-T246174", "Noise-TA120-T246182"],
    "viikkisolar": [f"ViikkiSolar-Inv{i}" for i in range(1, 9)],
    "lvdt": ["wapicelvdt"]
}


def extract_timestamp_from_query(query_parameters, param_name, default_timestamp):
    return (
        datetime.strptime(query_parameters[param_name], "%Y-%m-%dT%H:%M:%SZ")
        if param_name in query_parameters
        else default_timestamp
    )


class Observation(Resource):
    def get(self):
        """
        gets list of all observations
        """

        DEFAULT_MIN_RESULTTIME = datetime.now() + timedelta(days=-2)
        #DEFAULT_MAX_RESULTTIME = datetime.now() + timedelta(days=+1)
        DEFAULT_MIN_PHENOMTIME = datetime.now() + timedelta(days=-2)
        DEFAULT_MAX_PHENOMTIME = datetime.now() + timedelta(days=+1)

        try:
            query_parameters = request.args
            obs_list = []
            if query_parameters:

                if "case" not in query_parameters:
                    result = {"message": "url rewrite error"}
                    response = jsonify(result)
                    response.status_code = 400
                    return response

                if "thing" in query_parameters:
                    thing = request.args["thing"]
                    case = request.args["case"]

                    if thing in allowed_things[case]:

                        minresulttime = extract_timestamp_from_query(
                            query_parameters,
                            "minresulttime",
                            DEFAULT_MIN_RESULTTIME,
                        )

                        DEFAULT_MAX_RESULTTIME = minresulttime + \
                            timedelta(days=+1)
                        maxresulttime = extract_timestamp_from_query(
                            query_parameters,
                            "maxresulttime",
                            DEFAULT_MAX_RESULTTIME,
                        )

                        minphenomtime = extract_timestamp_from_query(
                            query_parameters,
                            "minphenomtime",
                            minresulttime,
                        )

                        DEFAULT_MAX_PHENOMTIME = minphenomtime + \
                            timedelta(days=+1)
                        maxphenomtime = extract_timestamp_from_query(
                            query_parameters,
                            "maxphenomtime",
                            DEFAULT_MAX_PHENOMTIME,
                        )

                        obs_list = Observations.filter_by_thing_timebound(
                            thing,
                            minresulttime,
                            maxresulttime,
                            minphenomtime,
                            maxphenomtime,
                        )

                    else:
                        result = {"message": " unrecognized 'thing' "}
                        response = jsonify(result)
                        response.status_code = 400
                        return response

                else:
                    result = {"message": "query parameters 'thing' expected"}
                    response = jsonify(result)
                    response.status_code = 400
                    return response
        except ValueError as e:
            logging.error(e)
            result = {"message": "timestamp error"}
            response = jsonify(result)
            response.status_code = 400
            return response

        except Exception as e:
            logging.error(e)
            result = {"message": "unexpected error"}
            response = jsonify(result)
            response.status_code = 400
            return response

        if obs_list:

            response = jsonify(obs_list)
            response.status_code = 200
            return response
        else:
            result = {"message": "No observations found"}
            response = jsonify(result)
            response.status_code = 200
            return response


api.add_resource(Observation, "/observation")
