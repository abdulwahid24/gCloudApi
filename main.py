from flask import Flask, request
from flask_restful import Resource, Api, abort
from flask_cors import CORS

from apiclient import discovery
from apiclient.http import MediaIoBaseUpload
from oauth2client.client import GoogleCredentials

import logging
# make your awesome app
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
api = Api(app)
cors = CORS(app)


ALLOWED_VIDEO_EXT = ["mp4", "m4v", "mov", "avi", "mkv", "x-msvideo", "octet-stream"]
		
class Video(Resource):

	def __init__(self):
		self.bucket_name = "bucket-videos"
		self.credentials = GoogleCredentials.get_application_default()
		self.service = discovery.build('storage', 'v1', credentials=self.credentials)

	def get(self):
		try:
			fields_to_return = 'nextPageToken,items(name,size,contentType, mediaLink,metadata(my-key))'
			req = self.service.objects().list(bucket=self.bucket_name, fields=fields_to_return)
			while req is not None:
				resp = req.execute()
				req = self.service.objects().list_next(req, resp)
		   	return resp
		except Exception as e:
			return abort(400, **{"message":e.message})

	def post(self):
		try:
			uploaded_file = request.files["fileUpload"]
			if uploaded_file.mimetype.split("/")[1] not in ALLOWED_VIDEO_EXT:
				abort(400, **{"message": "Invalid file format."})
			file_media = MediaIoBaseUpload(uploaded_file, mimetype=uploaded_file.mimetype, chunksize=1024*1024, resumable=True)
			req = self.service.objects().insert(
				bucket=self.bucket_name,
				name= str(uploaded_file.filename).encode('utf8'),
				predefinedAcl="publicRead",
				media_body=file_media)
			resp = req.execute()
			return {"success": True, "resp": resp}
		except Exception as e:
			error = e.data if 'data' in e.__dict__ else {"success":False, "message":e.content}
			abort(400, **error)

api.add_resource(Video, '/videos')

if __name__ == '__main__':
    app.run(debug=True)