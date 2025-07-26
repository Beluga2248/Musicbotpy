// Load environment variables
require('dotenv').config();

const { Client, GatewayIntentBits, Collection } = require('discord.js');
const { joinVoiceChannel, createAudioPlayer, createAudioResource, AudioPlayerStatus } = require('@discordjs/voice');
const ytdl = require('ytdl-core');
const ffmpegStatic = require('ffmpeg-static'); // This package helps find ffmpeg

// Check if token is loaded
const TOKEN = process.env.DISCORD_TOKEN;
if (!TOKEN) {
    console.error("Error: DISCORD_TOKEN not found in .env file. Please create a .env file and add DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE");
    process.exit(1);
}

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent, // REQUIRED for reading message content
        GatewayIntentBits.GuildVoiceStates // REQUIRED for voice
    ]
});

client.commands = new Collection();
const player = createAudioPlayer();
let connection = null; // Store the voice connection

client.once('ready', () => {
    console.log(`Logged in as ${client.user.tag}!`);
    console.log('------');

    // Event listener for audio player status
    player.on(AudioPlayerStatus.Idle, () => {
        console.log('Audio player is idle, song finished or stopped.');
        // Optionally, you could make the bot leave after a song
        // if (connection) {
        //     connection.destroy();
        //     connection = null;
        //     console.log('Left voice channel after song finished.');
        // }
    });

    player.on('error', error => {
        console.error('Error in audio player:', error);
    });
});

client.on('messageCreate', async message => {
    // Ignore messages from bots and messages not starting with the prefix
    const prefix = '!';
    if (!message.content.startsWith(prefix) || message.author.bot) return;

    const args = message.content.slice(prefix.length).trim().split(/ +/);
    const command = args.shift().toLowerCase();

    // --- Join Command ---
    if (command === 'join') {
        if (!message.member.voice.channel) {
            return message.reply('You need to be in a voice channel to make me join!');
        }

        try {
            connection = joinVoiceChannel({
                channelId: message.member.voice.channel.id,
                guildId: message.guild.id,
                adapterCreator: message.guild.voiceAdapterCreator,
                selfDeaf: false, // Set to true if you want the bot to be deafened
            });
            console.log(`Joined voice channel: ${message.member.voice.channel.name}`);
            message.channel.send(`<a:Yes:1011614293420150805> Joined voice channel: **${message.member.voice.channel.name}**`);

            // Subscribe the connection to the player
            connection.subscribe(player);

        } catch (error) {
            console.error('Error joining voice channel:', error);
            message.channel.send('<a:Wrong:1017416697168269372> There was an error trying to join the voice channel.');
        }
    }

    // --- Play Command ---
    else if (command === 'play') {
        if (!connection) {
            return message.reply('<a:Wrong:1017416697168269372> I am not connected to a voice channel. Use `!join` first.');
        }

        const url = args[0];
        if (!url || !ytdl.validateURL(url)) {
            return message.reply('<a:Wrong:1017416697168269372> Please provide a valid YouTube URL!');
        }

        try {
            message.channel.send(`Attempting to play: ${url}`);
            const stream = ytdl(url, { filter: 'audioonly', quality: 'highestaudio' });
            const resource = createAudioResource(stream, {
                inputType: require('@discordjs/voice').StreamType.Arbitrary,
                inlineVolume: true // Allows setting volume on the resource
            });
            player.play(resource);
            console.log(`Now playing: ${url}`);
            message.channel.send(`<a:Playing_Audio:1011614261560221726> Now playing: **${url}**`);

        } catch (error) {
            console.error('Error playing audio:', error);
            message.channel.send('<a:Wrong:1017416697168269372>There was an error trying to play the audio. Make sure the URL is valid.');
        }
    }

    // --- Leave Command ---
    else if (command === 'leave') {
        if (connection) {
            player.stop(); // Stop any playing audio
            connection.destroy(); // Destroy the voice connection
            connection = null;
            message.channel.send('<a:Yes:1011614293420150805>Left the voice channel.');
            console.log('Left voice channel.');
        } else {
            message.channel.send('<a:Wrong:1017416697168269372>I am not in a voice channel.');
        }
    }

    // --- Stop Command ---
    else if (command === 'stop') {
        if (player.state.status !== AudioPlayerStatus.Idle) {
            player.stop();
            message.channel.send('Stopped current playback.');
            console.log('Playback stopped.');
        } else {
            message.channel.send('<a:Wrong:1017416697168269372>Nothing is currently playing.');
        }
    }
});

// Login to Discord with your client's token
client.login(TOKEN);
