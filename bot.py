require('dotenv').config();
console.log('Starting bot...');
console.log('Token exists:', !!process.env.DISCORD_TOKEN);

const http = require('http');
http.createServer((req, res) => res.end('Bot is running!')).listen(process.env.PORT || 3000);
console.log('HTTP server started');

process.on('unhandledRejection', (error) => {
  console.error('Unhandled rejection:', error);
});

const { Client, GatewayIntentBits, Partials, EmbedBuilder } = require('discord.js');

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.GuildMessageReactions,
    GatewayIntentBits.MessageContent,
  ],
  partials: [Partials.Message, Partials.Channel, Partials.Reaction],
});

const config = require('./config.js');

client.once('ready', () => {
  console.log(`✅ Logged in as ${client.user.tag}`);
});

client.on('shardDisconnect', () => {
  console.log('⚠️ Bot disconnected, reconnecting...');
  client.login(process.env.DISCORD_TOKEN);
});

client.on('interactionCreate', async (interaction) => {
  if (!interaction.isChatInputCommand()) return;
  const { commandName } = interaction;
  if (!interaction.member.permissions.has('Administrator')) {
    return interaction.reply({ content: '❌ You need Administrator permission.', ephemeral: true });
  }
  if (commandName === 'setuproles') {
    const embed = new EmbedBuilder()
      .setTitle(config.embedTitle)
      .setDescription(config.embedDescription)
      .setColor(config.embedColor);
    const msg = await interaction.channel.send({ embeds: [embed] });
    for (const { emoji } of config.reactionRoles) {
      await msg.react(emoji);
    }
    config.reactionMessageId = msg.id;
    config.reactionChannelId = interaction.channelId;
    await interaction.reply({ content: `✅ Done! Message ID: \`${msg.id}\``, flags: 64 });
  }
});

client.on('messageReactionAdd', async (reaction, user) => {
  if (user.bot) return;
  if (reaction.message.partial) await reaction.message.fetch();
  if (reaction.message.id !== config.reactionMessageId) return;
  const entry = config.reactionRoles.find(r => r.emoji === reaction.emoji.name || r.emoji === reaction.emoji.toString());
  if (!entry) return;
  const guild = reaction.message.guild;
  const member = await guild.members.fetch(user.id);
  const role = guild.roles.cache.get(entry.roleId);
  if (role) await member.roles.add(role);
});

client.on('messageReactionRemove', async (reaction, user) => {
  if (user.bot) return;
  if (reaction.message.partial) await reaction.message.fetch();
  if (reaction.message.id !== config.reactionMessageId) return;
  const entry = config.reactionRoles.find(r => r.emoji === reaction.emoji.name || r.emoji === reaction.emoji.toString());
  if (!entry) return;
  const guild = reaction.message.guild;
  const member = await guild.members.fetch(user.id);
  const role = guild.roles.cache.get(entry.roleId);
  if (role) await member.roles.remove(role);
});

console.log('Calling client.login...');
client.login(process.env.DISCORD_TOKEN);

