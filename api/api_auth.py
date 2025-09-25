from datetime import timedelta , datetime , timezone
from typing import Annotated
import os # os import
from aiohttp.web import HTTPExpectationFailed
from requests import status_codes
from typing_extensions import runtime

from fastapi import Depends , HTTPException , status , APIRouter
from pydantic import BaseModel 
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from starlette.status import HTTP_400_BAD_REQUEST
import logging

from dotenv import load_dotenv
from api.utils.dependancies import ALGORITHM, SECRET_KEY, bcrypt_context , db_dependancy , refresh_user_dependancy
from pydantic_schemas.users_schema import Token , UserCreateRequest
from api.utils.util_users import create_user , get_user_by_username , get_user_by_email

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix = '/auth',
    tags = ['auth']
)

SECRET_KEY = os.getenv('AUTH_SECRET_KEY')
ALGORITHM = os.getenv('AUTH_ALGORITHM')
REFRESH_ALGORITHM = os.getenv('REFRESH_ALGORITHM')

# now we are going to create some functinality for the authentication itself 
# user auth function 

async def authenticate_user(username: str, password: str, db):
    user = await get_user_by_username(db, username)
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

# now lets build another function for generating the authentication token 

async def create_access_token( username : str , user_id : int , expires_delta : timedelta ):
    encode = {'sub' : username , 'id' : user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp' : expires})
    return jwt.encode(encode , SECRET_KEY , algorithm = ALGORITHM) # and just like that we will have created the access token 

async def create_refresh_token(username : str , user_id : int , expires_delta : timedelta):
    encode = {'sub' : username , 'id' : user_id }
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp' : expires})
    return jwt.encode(encode , SECRET_KEY , algorithm = REFRESH_ALGORITHM)

# ENDPOINTS
#this endpoint is for creating a new user to the database and the system 
@router.post('/' , status_code = status.HTTP_201_CREATED)
async def add_user( db : db_dependancy , user : UserCreateRequest):
    """
    fetch database to confirm that user is not duplicate by confirming the email
    fetch chess.com database to confirm validility of account
    if valid create both user profle and chess profile for the user 
    create a new user with the created credentials
    """
    db_user = await get_user_by_email(db , user.email)
    if db_user:
        raise HTTPException( status_code = status.HTTP_409_CONFLICT , detail = "email is already registered")
    # fech user data to confirm validility of the account on chess.com
    if user.chessDotComUsername :
        try : 
            chess_service_instance = ChessPlayerService(user.chess_username)
            user_chess_data = await chess_service_instance.fetch_user_profile_data() # error handing for the response is already done in the chessprofileservice itself 
            # after fetching the chess user data the next step is to add the data to the database of which we have down down here after the creating a new user to the database
        except Exception as e:
            logger.error(f'the chessprofile service failed {e}')
            raise RuntimeError(f'the chess service failed')
        #on successful fetch of the chess user data i belive its not time to create populate the database with relevant data for the users using their chess.com username as their username
        new_db_user = await create_user(db , user)
        if not new_db_user:
            raise RuntimeError(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR , detail = f"failed to create a new user database object")
        new_db_chess_profile_foreign = await add_new_chess_player(user_chess_data)
        if not new_db_chess_profile_foreign :
            raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR , detail = f"failed to create a chess.com profile on database")
        print("user and related object created successfuly")
        token = await create_access_token(new_db_user.username , new_db_user.id , timedelta(minutes=20))
        return {'access_token' : token , 'token_type' : 'bearer' }

    else :
        print(f'no chess username was provided thus no need to add fetch chess user data')
        # create a new user profile in the database using the non_chess.com username
        new_db_user = await create_user(db , user)
        if not new_db_user:
            raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR , detail = f"failed to create a chess profile for the normal non chess.com username")
        # by this point the native profile will have been created in the create user utility function 
        # and thus the only thing left i think will be return the access token 
        token = await create_access_token(new_db_user.username , new_db_user.id , timedelta(minutes = 20))
        return {'access_token' : token , 'token_type' : 'bearer'}
        
# lets create another endpoint for getting the access token and sedning it back to the user
@router.post('/token' , response_model = Token , status_code = status.HTTP_201_CREATED)
async def login_for_access_token( 
    form_data : Annotated[OAuth2PasswordRequestForm , Depends()] , # this oauth2 thingy here is just a way for us to get login details by following th estandard for auth , its better than just sendin the raw json data : username : str and password : str 
    db : db_dependancy ):
    user = await authenticate_user(form_data.username , form_data.password , db )
    if not user:
        raise HTTPException( status_code =status.HTTP_401_UNAUTHORIZED , detail = " could not authorize the user , the dtails that you have entered are not correct check details please  ")
        raise RuntimeError( status_code=status.HTTP_401_UNAUTHORIZED , detail = 'the dtails that you have entered are not correct check details please ')
    access_token = await create_access_token(user.username , user.id , timedelta(minutes = 20))
    refresh_token = await create_refresh_token(user.username , user.id , timedelta(minutes=10080))
    return {
        'access_token' : access_token ,
        #'refresh_token' : refresh_token , 
        'token_type' : 'bearer'
         }

# we are now going to create a nll use it iew endpoint for generating a new access tokne whenver the previous one expires 
@router.post('/token/refresh' ) # so this neans when querying this endpoint we structure it this way : /auth/token/refresh and this is based on the prefix at the start of the file 
async def get_new_access_token(data : refresh_user_dependancy):
    username = data.get('username')
    user_id = data.get('id')
    print("we are now extracting user data from the ")
    if username is None or user_id is None:
        raise HTTPException( status_code = status.HTTP_401_UNAUTHORIZED , detail = "error authenticating user")
    new_access_token = await create_access_token(username , user_id , timedelta(minutes = 20))
    return {'access_token' : new_access_token , 'token_type' : 'bearer' }

# note : this endpoint created here we will use it in future requests when building the other secure endpoints 