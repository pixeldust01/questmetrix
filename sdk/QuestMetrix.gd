extends Node

var api_base_url: String = "http://127.0.0.1:8000"
var game_id: String = "godot_test_game"
var player_id: String = "godot_player_001"

var http_request: HTTPRequest

func _ready():
	http_request = HTTPRequest.new()
	add_child(http_request)

	http_request.request_completed.connect(_on_request_completed)


func track(event_name: String, extra_data: Dictionary = {}) -> void:
	var event_data = {
		"event": event_name,
		"player_id": player_id,
		"game_id": game_id,
		"timestamp": Time.get_datetime_string_from_system(false),
		"level": 1
	}

	# for adding extra [optional] game data. eg: extra parameters while 
	# tracking character/game object data
	for key in extra_data:
		event_data[key] = extra_data[key]

	var json_body = JSON.stringify(event_data)

	var headers = [
        "Content-Type: application/json"
	]

	var error = http_request.request(
		api_base_url + "/events",
		headers,
		HTTPClient.METHOD_POST,
		json_body
	)

	if error != OK:
		print("QuestMetrix: Failed to start HTTP request. Error code: ", error)

func _on_request_completed(result, response_code, headers, body):
	if result != HTTPRequest.RESULT_SUCCESS:
		print("QuestMetrix: Failed to reach backend. Error code: ", result)
		return

	if response_code < 200 or response_code >= 300:
		print("QuestMetrix: Backend returned HTTP status ", response_code)
		return

	print("QuestMetrix: Event sent successfully.")
