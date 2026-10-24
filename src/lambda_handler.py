import logging
from agent import agent

# Global initialisation

logger = logging.getLogger()
logger.setLevel("INFO")

#  Define entry point

def lambda_handler(event, context):

    # Unpack prompt
    user_prompt = event.get('prompt')
    if not user_prompt:
        raise ValueError('user_prompt is not availble, pls re-prompt')

    response = agent(user_prompt)

    # Output result
    return {
        "statusCode": 200,
        "message": str(response)
    }