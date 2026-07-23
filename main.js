const { Client } = require('whatsapp-web.js');


const client = new Client();
const qrcode = require('qrcode-terminal')

// When the client is ready, run this code (only once)
client.once('ready', () => {
    console.log('Client is ready!');
});

// When the client received QR-Code
client.on('qr', (qr) => {
    console.log('QR RECEIVED', qr);
     qrcode.generate(qr, {small: true});
});

// Start your client
client.initialize();

// Listening to all incoming messages
client.on('message_create', message => {
	console.log(message.body);
});

client.on('message_create', message => {
    greeting = 
    "*Welcome to sherlock !* 🔍 \n I am your virtual assistant who helps you to : \n 1. Search any Lecturer by name to find their phone number. \n 2. Add lecturer's details so others can find them."

	if (message.body === 'Hello') {
		// greeting message 
		client.sendMessage(message.from, greeting);
	}
});


