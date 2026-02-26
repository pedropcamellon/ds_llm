# [Guide] Getting started with modding DST (and some general tips for DS as well)

rezecib
By rezecib,
December 22, 2014 in Tutorials and Guides

Posted December 22, 2014
Try to keep the "I have a problem with my mod" posts to their own topics. I read literally everything in this subforum, so I will see it.

First off, I know this is a really long post. The thing is, modding is complicated, and there are a bajillion directions you can go with it, so just trying to cover the basics is still quite a lot of stuff. I tried to organize it so that you can skip to parts that are relevant to you, though. Unfortunately, I don't think I can fix the within-post links, which worked in the old forum software but there doesn't seem to be a way to repair them now.

If you're skipping this because it's too long, or are only going to skim for parts you want, here's the minimal set of things I recommend you read:

Spoiler
LuaGuideObjects'>Tables as objects (and how to modify their functions nicely) (this is under the Lua Guide, and you'll have to open its spoiler before the link to it will work)

Reading the code

Start with another mod or game files

Guides for specific new things in DST

Selected useful guides from the single-player mod forums


## Introduction

General Advice

Basic Lua guide (you have to open the spoiler for this before you can jump to its sub-entries)

LuaGuideLooseTyping'>Loose Typing

LuaGuideMinimal'>Minimal Evaluation

LuaGuideTables'>Tables

LuaGuideObjects'>Tables as objects (and how to modify their functions nicely)

Reading the code

Start with another mod or game files

Tips on fixing crashes

Transitioning from Don't Starve to Don't Starve Together

Using the same code for both games

New TheThings

New stuff in the modinfo

List of things that are mosty the same (with notes on minor differences)

Differences

New things in prefabs

Informal explanation of major engine differences (replicas, classifieds, netvars, and RPCs)

Component Actions

Other miscellaneous differences

List of things that are currently not (nicely) moddable

Other guides for DST

Selected useful guides from the single-player mod forums

Introduction
I decided to write this modding tutorial because when I was getting started modding, none of the tutorials really did it for me. I don't want to devalue the effort that was put into the other tutorials-- and there are many (here's a compilation of guides for DS), and many of them are great at explaining how to do specific things. The reason why there aren't any good tutorials on generally getting started is that getting started is actually really hard, and there are a lot of directions you could go, so it's really hard to cover them all. Hopefully this tutorial at least helps with that a little.

General Advice

I think most people get started with an idea. So you have a thing you'd like to mod into the game, maybe a new item or character. How do you get started?
 
Well, the first thing is you have to know how to write code (that is, in general, in any language). There are lots of tutorials/lessons/etc around the internet for learning that.
 
Next, you need to be able to read and write Lua code specifically. Personally, being told to "go learn Lua" isn't something that works for me. If it does for you, then definitely go do that! It'll probably give you a well-rounded understanding of the language. If it doesn't work for you, though, then you probably need to dig into some existing Lua code. The best place to do that is the game's code. Think of things in the game that are similar to what you want to do, find them in the files, and keep reading/poking at them until you understand how they work. At first, this will be hard-- there are aspects to Lua you may not understand. You'll just have to look them up as you go. As for general information on how the game logic is put together, the thing that I found most helpful was Wots The Diff??.

 

Basic Lua Guide

A few aspects of Lua are really, really important, though, so I've written a little very informal guide on some of them:

Spoiler
Loose typing:

Spoiler
This means that unlike Java or C, a given variable isn't explicitly an "int" or "bool" or whatever. Technically they are under the hood, and you can check that with code like this:



local message = "hi"print( type(message) )-- prints out "string"
One of the advantages of loose typing is that things are free to be interpreted how they need to. For example, you can use every other type like a boolean (that is, a true/false value). The way Lua handles this is that anything that is not false or nil is interpreted as true. This will be useful later when I've talked about minimal evaluation.

Minimal evaluation (or short-circuit evaluation):

Spoiler
Lua will only evaluate code up to the point where it needs to. One way this gets used is in boolean expressions that may not actually be with boolean values. For example, if you have a character stored in player, they will have a components entry in their table (I will talk about tables below), and components will be a table of components. Maybe you're not sure if a particular component exists (yet). You can use a structure like this to make sure the code doesn't crash:



if player and player.components and player.components.firebug then
	--[[do stuff]]
end
Otherwise, if player was nil, and you tried to run player.components, it would crash. Minimal evaluation saves you because if player is nil, it will stop there, because if player is nil, then it interprets it as false, and any boolean statement that's composed of false followed by ands is always going to be false. A humorous example: Do you have cookies, cake, and pie? Well, if you're lacking any one of those, then the answer is no. So it checks cookies first, and if you don't have cookies, then it can conclude the answer is no already without having to check for cake or pie.
 
I want to cover one use of minimal evaluation specifically, because it's something you'll probably see fairly often, and it's not immediately obvious how it works (it's an idiom). It goes like this:



local thing = condition and if_true or if_false
This is equivalent to the following:



local thing = nil
if condition and if_true then
    thing = if_true
else
    thing = if_false
end
If if_true is not nil or false, though, then it's equivalent to the more intuitive code that follows:



local thing = nil
if condition then
    thing = if_true
else
    thing = if_false
end 
 

Tables:

Spoiler
Tables are probably the most unique aspect of Lua. They handle a lot of different data structures all in one, particularly maps and arrays. A table is filled with key-value pairs. If you give the table a key, it will give you the value that's paired with that key. You can do this either of the following ways:



my_table.key = "value"
my_table["key"] = "value"
The second way lets you have the key in a variable, which is mainly handy if you want to loop through the pairs in a table and use them to access things in another table. For the most part, though, in the game's code they already know what part of the table they want, so they'll use the my_table.key approach. Here's an example of declaring a table (this is from the game's tuning.lua, where it's specifying what tech a science machine gives):



SCIENCEMACHINE =
{
    SCIENCE = 1,
    MAGIC = 1,
    ANCIENT = 0,
}
So if you want to check what level of science the science machine gives, you'd check SCIENCEMACHINE.SCIENCE (although in the game this is located in a couple of other tables, so the full thing is TUNING.PROTOTYPER_TREES.SCIENCEMACHINE.SCIENCE). You can also add more pairs to the table after the declaration, for example:



SCIENCEMACHINE.BOMBS = 1
The way tables also work as arrays is by having integer keys. Normally you get a value from an array by giving it the index; in this case, you do the same, but under the hood the index happens to be a key. Here's an example of using a table as an array (this was the game's list of characters when DST first entered closed beta):



DST_CHARACTERLIST = { "wilson", "willow", "wx78", "wickerbottom" }
In this case, DST_CHARACTERLIST[1] == "wilson", DST_CHARACTERLIST[2] == "willow", and so on. (for programmers coming from other languages, Lua uses 1-based indexing, so the first index is 1 instead of 0).
 
Now, tables are great for organization and all, but the main reason to use them is for iteration. Often you'll want to iterate through all the pairs in a table. The most convenient way to do this is with a for loop like this:



for k,v in pairs(SCIENCEMACHINE) do
    -- do stuff to the k (key) and v (value) pair that it got from the table
    -- in this loop, my_table[k] == v
    -- one loop has k == "SCIENCE", v == 1
    -- one loop has k == "MAGIC", v == 1
    -- one loop has k == "ANCIENT", v == 1
    -- one loop has k = "BOMBS", v = 1
end
In Lua in general, the ordering of these is not guaranteed. However, the interpreter used by the game goes through them in the order they were added. Note that the "k,v" part can be changed-- you can use any variable names you want for k and v instead. It's just convention to use k,v because they're short and correspond to the "key" and "value" terms.
 
Sometimes, however, you want to iterate through a table like an array. For that, we use ipairs instead.



for i,v in ipairs(DST_CHARACTERLIST) do
    -- do stuff to the i (index) and v (value) pair that it got from the table
    -- the first loop has i == 1, v == "wilson"
    -- the first loop has i == 2, v == "willow"
    -- the first loop has i == 3, v == "wx78"
    -- the first loop has i == 4, v == "wickerbottom"
end
 
One neat thing about tables is that you can actually use both of these approaches at once. One place the code uses this is for the introductory speeches Maxwell gives at the start of each Adventure Mode world (you'll have to play single-player to see this). You can look at this in the maxwellintro.lua file, but I'm going to cut down the table I show here a bit so it's smaller.



NULL_SPEECH=
{
    voice = "dontstarve/maxwell/talk_LP",
    appearanim = "appear",
    {
        string = "There is no speech number.", --The string maxwell will say
        wait = 2, --The time this segment will last for
        anim = nil, --If there's a different animation, the animation maxwell will play
        sound = nil, --if there's an extra sound, the sound that will play
    },
    {
        string = nil,
        wait = 0.5,
        anim = "smoke",
        sound = "dontstarve/common/destroy_metal",
    },
}
So, in this case we have some of the table being declared like a map (with keys and values), and some of it being declared like an array (with just values one after the other). The list part is given normal list keys-- in this case, the numbers 1 and 2. So if we use both methods of iterating on this table...



for k,v in pairs(NULL_SPEECH) do
    -- first loop has k == "voice", v == "dontstarve/maxwell/talk_LP"
    -- second loop has k == "appearanim", v == "appear"
    -- third loop has k == 1, and v is the first little table there, with v.wait == 2
    -- fourth loop has k == 2, and v is the second little table, with v.wait == 0.5
end
for i,v in ipairs(NULL_SPEECH) do
    -- first loop has i == 1, and v is the first little table there, with v.wait == 2
    -- second loop has i == 2, and v is the second little table, with v.wait == 0.5
end
 

Tables as objects (and how to modify their functions nicely):

Spoiler
I'll start this part with a really quick pointer: if you can at all avoid it, do not replace the game's files with new versions in your mod (for example, you have scripts/components/eater.lua in your mod). If you mod does this, it will be incompatible with any other mod that does. If at all possible, you should modify specific functions of an object in the way that I show lower down in this section (that is, store the old version, replace it with a new version that calls the old version, and make sure to return the result of the old version).

Now, objects in the game all get built into a resulting table, which can then be modified. For example, a player's information and functions are all stored in a table. Most of the time you'll be working with prefab tables, which have a components table within them, as well as a reference to a stategraph object/table, and a brain object/table (see Wots The Diff?? for what those things are). I talked a lot about key/value pairs in a table, but this also goes for functions. In Lua, a function can be stored in a variable. One place (of many) where this gets used is in creating characters. You'll notice in willow.lua that it makes two functions, common_postinit, and master_postinit, and then it's giving these functions as arguments/parameters to the MakePlayerCharacter function. Unlike, say, Java, when a function is part of an object there isn't really anything special about it-- it's just a variable stored in that object's table. For example, every entity has this function:



inst:GetPosition()
But GetPosition is just a variable that's stored in inst, like so:



inst.GetPosition = function(...) --[[some mysterious code]] end
When you see ":" being used instead of ".", all it's doing is this:



inst.GetPosition(inst) -- the same as inst:GetPosition()
This is called "syntactic sugar", which just means that it's a convenient shorthand way of writing it, but they're actually the same. So, for example, you could replace the GetPosition function by taking advantage of the fact that it's a variable:



local OldGetPosition = inst.GetPosition
inst.GetPosition = function(thing)
    local pos = OldGetPosition(thing)
    pos.x = math.floor(pos.x+0.5)  
    pos.y = math.floor(pos.y+0.5)  
    pos.z = math.floor(pos.z+0.5) 
    return pos
end
What this does is store the old GetPosition function, then replace it with a new one that rounds the position coordinates to whole numbers.

 
The ability to modify functions in this manner is one of the most useful modding tools Lua provides. I'll talk later a bit about different ways you can go about modding, and why you should use this approach whenever possible. (although don't actually modify GetPosition. Everything uses that, so it would probably cause a ton of problems!)

Reading the code

Next, you have to be able to read the game's code. I can't stress this enough; how can you expect to mod something if you can't even go about figuring out how it works in the first place? You don't have to understand how ALL the code works, but you need to be able to understand at least the part you're modifying. I think the biggest problem people have here is that they don't know how to go about looking at the game's code. So I'll give some recommendations.

Spoiler
The game's code is located here for me (it should be somewhere similar for you, but you can at least get to the Don't Starve Together Beta folder through Steam-- Properties > Local Files > Browse Local Files):


C:\Program Files (x86)\Steam\SteamApps\common\Don't Starve Together Beta\data\scripts
Use Notepad++ (or another coding text editor, if you already have one you like). Editors like Notepad++ will color the code to make it easier to read, as well as having lots of useful features like tabs for separate files, side-by-side views of files, hotkeys for commenting/uncommenting, and find-in-files. Find-in-files is pretty much the most powerful tool at your disposal, because the game is complicated and files refer to each other from far away, and it's not always immediately obvious what other file they're getting stuff from. So if you see a value or a function and it's not declared anywhere if the file you're looking at, do a find-in-files search for it. For example, let's say you're looking at willow.lua to see how characters are made. You see this line:


inst.components.sanity:SetMax(TUNING.WILLOW_SANITY)
But there's no TUNING table there, and no WILLOW_SANITY anywhere you see. If you do find-in-files for WILLOW_SANITY in the game's scripts folder, you'll see that there's a tuning.lua that has a (very huge) table TUNING, in which WILLOW_SANITY = 120.

Using find-in-files to find function declarations is usually a bit more work, because the function will be used many places in the code, but only declared in one. So you can either skim through the results to see where it says "function ThisIsTheFunctionYouAreLookingFor(stuff)", or you can use a regular expression find-in-files. In Notepad++ you do this by going to the normal find-in-files place (a tab in the ctrl+F box), then at the bottom there's a selection for "Regular expression". Then adjust your find-in-files search to look like this: "function.*ThisIsTheFunctionYouAreLookingFor". The ".*" basically means "and anything can be between these, as long as these are both on the same line and in that order".

When people ask me for help with their mods, or help with console commands for the game or whatever, there's a 90% chance I don't know off the top of my head. Most of the time, what I'm doing is just using find-in-files, and then reading the code. And you can do it too!

The only place find-in-files will fall short is when a function you're looking for is defined in the C++ code. Functions on the objects TheSim, TheNet, TheWorld.minimap.MiniMap, AnimState, and a few others are defined in the C++ code. As modders, we can't really modify these, and all we have to go on in terms of how to use them is how they're used in the rest of the Lua code. PeterA and MarkL have said they're working on an API for these objects, so hopefully they will become demystified a bit soon. Looks like that must've been abandoned :(

Start with another mod or game files

Once you're about to start writing the code for the mod, I wouldn't recommend just starting completely fresh. It's way simpler and easier to take the most similar mod you know of, or the most minimal mod you know of, copy that folder, then rename and change things. This ensures you have all the pieces you need (modmain, modinfo, etc), and then you can see what you need to change.

Similarly, when you're making a new item or creature, start by copying over the most similar item/creature from a mod or the game files. This ensures that you aren't missing crucial stuff. So, for example, you want to make a new equippable; start by copying over spear.lua, and look at a mod that adds an item to see that you need to add it to the PrefabFiles table in the modmain. Once you have the copy, you can start renaming things and changing the assets or properties.

Tips on fixing crashes

Spoiler
When the game crashes, it almost always leaves a very helpful message in Documents/Klei/DoNotStarveTogether/log.txt (it will usually also show this message on an error screen). Personally, I keep this file open in Notepad++ all the time, because I need to use it all the time. Here's part of a crash I just produced in a mod intentionally:

  Reveal hidden contents
You can see that it's saying the crash occurs in the MoreMapIcons modmain.lua, at line 93. So the first thing you should do is go there and see what's written. The next piece of important information is the "attempt to index global 'ThePlayer' (a nil value)" part. This is actually one of the most common crashes-- attempting to index nil values. What this means is that I wrote something like one of these two lines:


ThePlayer:AddComponent("firebug")
ThePlayer.components
But ThePlayer was nil. In this case, I need to be using GLOBAL.ThePlayer, because the modmain runs in a sandbox so that you don't accidentally overwrite variables in the global space of the game. When you run into an "attempt to index nil" crash, you just need to find out why the value is ending up nil there, and make sure that doesn't happen. To this end, the crash stack traceback is quite useful-- it shows you what function was running when it started running the modmain, and the function that was running that, etc. In this case it's not that useful, because the error doesn't exist in the mod's loading system, it exists directly in the modmain, but for more complex mods it can be very helpful to see what functions were called to get there, because that will give you more information on how the variable could've ended up nil.

As you learn more about how the game works (prefabs, components, replicas, etc), it will become easier to follow the flow of information to diagnose problems like this.

 

Transitioning from Don't Starve to Don't Starve Together

So all of that covers most of the stuff I can think of for how to generally approach modding. Now let's cover the differences from DS to DST (because there are plenty of tutorials for how to do specific stuff in DS).

Using the same code for both games

Spoiler
Although some of the mod changes were made with the idea of encouraging maintaining separate versions of mods for each game, in some cases you may want to use the same code for both (particularly if almost all the code is the same). You can determine if the code is being run by DST with the following check:


TheSim:GetGameID() == "DST" 
The details on where you should be using this to switch between different code blocks is much trickier, but hopefully the later sections shed some light on it.

 

Additionally, because the two games have different mod API versions, you can specify each independently in the modinfo:


api_version = 6
api_version_dst = 10 
Don't Starve checks only api_version, while Don't Starve Together will use api_version_dst if it exists, or api_version if it does not (so for DST-only mods, you can just use api_version if you want).

New TheThings

Spoiler
GetWorld() is now TheWorld instead, and GetPlayer() is now ThePlayer. That's pretty simple. The main thing to keep in mind is that the new ones are not functions, they're variables. So no "ThePlayer()". That will crash. Also, if you're updating a mod, don't just find-and-replace GetPlayer() with ThePlayer, because now there are multiple players, so you do need to look at each of those cases and see how you can get the particular player that you actually want it to interact with.

 TheNet is the only one that's completely new, and here are the functions it has that I've found useful so far (this is a bit out of date):


TheNet:GetIsServer() -- this is running on a computer hosting the game
TheNet:GetIsClient() -- this is running on a computer joining a game
TheNet:IsDedicated() -- for dedicated servers
TheNet:Announce(message) -- Announces a message at the top of the screen, like for deaths
TheNet:Say(message, whisper) -- Sends message in chat, and whispers it if whisper is true
Note that much of the code uses TheWorld.ismastersim instead of TheNet:GetIsServer() (and "not TheWorld.ismastersim" instead of TheNet:GetIsClient()). Most of the time, these are interchangeable, but there are some places where TheWorld.ismastersim hasn't been populated yet, so it will crash.

There are many other functions in TheNet, but these are the main ones I've found use for. You can find a bunch more in playerstatusscreen.lua, but I'm not sure they're useful enough for modding in general to list here.

Related to TheNet, sometimes the least-invasive way to change something is to modify the function SendRPCToServer. This is what most of the client-to-server communication goes through (RPC = remote procedure call, basically calling a function on the server). However, this should be a method of last resort, because you can really mess stuff up if something goes wrong!

New stuff in the modinfo

Spoiler

api_version = 10

api_version_dst = 10 -- optional (if it's the same mod for DST and single-player)

dst_compatible = true

--This lets clients know if they need to get the mod from the Steam Workshop to join the game
all_clients_require_mod = true

--This is basically the opposite; it specifies that this mod doesn't affect other players at all, and if set, won't mark your server as modded
client_only_mod = false

--This lets people search for servers with this mod by these tags
server_filter_tags = {"character", "rog", "reign of giants"}
 

List of things that are mosty the same (with notes on minor differences)

Spoiler
Art Assets. Keep in mind if you have custom assets, you need all_clients_require_mod = true.
AddPrefabPostInit, AddComponentsPostInit, etc. One thing to watch out for here, though, is that a lot of people were modifying the player in an AddSimPostInit. This doesn't fly anymore because the player doesn't exist yet there, so you should be doing this in another way--which way depends on the mod. If you're modifying the UI, do AddClassPostConstruct on playerhud, for example. Another thing to note is that the replicas have to be accessed with AddClassPostConstruct, even though they're in the components folder. For example, AddClassPostConstruct("components/builder_replica", function(self) --[[do stuff]] end). Classifieds, however, are still accessed with AddPrefabPostInit.
Most UI stuff. I noticed a lot of AddSimPostInits for these, though, so that's bad. It was probably not a good idea before, but it'll most likely crash now.
Adding Actions. The way that they are collected based on components is different, now, though-- instead of using a CollectUseActions or whatever in the component, you need to use AddComponentAction. A little more on that in the differences section below.
Probably a few more things that I'm not thinking of at the moment, or that I haven't worked with yet.
 

Differences

New things in prefabs

Spoiler

inst:AddNetwork() 
This needs to be in any entity that you want to create on the server and have it show up for all players. Most things have this, but in a few cases you want things to only exist on the server (e.g. meteorspawners, which are invisible), and in some very rare cases you may want to create things independently on each client.


    if not TheWorld.ismastersim then
        return inst
    end 
This is really important for almost all prefabs. This essentially says "if this is running on the client, stop here". Almost all components should only be created on the server (the really important ones will get replicated to the client through the replica system). Visual things and tags that will always be added can go above this, though.


    inst.entity:SetPristine() 
This basically says "everything above this was done on both the client on the server, so don't bother networking any of that". This reduces a bit of the bandwidth used by creating entities. I can't think of a case where you wouldn't want this immediately after the "if not TheWorld.ismastersim then return inst end" part, which is where you'll see it in the game's code.

Okay, so that's a bunch of pieces, but how do they fit together? Well, you should be referring directly to the most similar thing in the game's code to what you want to create. As I talk about above, when making a new thing in your mod, you should be starting by copying the most similar thing from another mod or the game files. However, just so you can take a look without leaving this guide, here's the constructor from spear.lua that shows how it fits together:


local function fn()
    local inst = CreateEntity()	
    inst.entity:AddTransform()
    inst.entity:AddAnimState()  
    inst.entity:AddNetwork()  
    MakeInventoryPhysics(inst)  
    
    inst.AnimState:SetBank("spear")  
    inst.AnimState:SetBuild("spear")  
    inst.AnimState:PlayAnimation("idle") 
    inst:AddTag("sharp")
    
    if not TheWorld.ismastersim then   
      return inst  
    end   
    
    inst.entity:SetPristine() 
    inst:AddComponent("weapon")
    inst.components.weapon:SetDamage(TUNING.SPEAR_DAMAGE)
    inst:AddComponent("finiteuses")  
    inst.components.finiteuses:SetMaxUses(TUNING.SPEAR_USES) 
    inst.components.finiteuses:SetUses(TUNING.SPEAR_USES)     
    inst.components.finiteuses:SetOnFinished(inst.Remove) 
    inst:AddComponent("inspectable")    
    inst:AddComponent("inventoryitem")   
    inst:AddComponent("equippable")  
    inst.components.equippable:SetOnEquip(onequip) 
    inst.components.equippable:SetOnUnequip(onunequip) 
    MakeHauntableLaunch(inst)   
    return inst
end 
 

 
Informal explanation of major engine differences (replicas, classifieds, netvars, and RPCs)

Spoiler
Like in single-player, on the host there are prefabs, which have components, stategraphs, and brains. On clients, however, things are quite different. Prefabs still exist, but usually only run a subset of their code. Only a few components exist, and only ones that have to deal with appearance-- such as talker, transparentonsanity, playercontroller, and playeractionpicker. Brains and stategraphs only exist on the host. In place of most components, clients have a bit of a mixed system of replicas and classifieds. Communication between the clients and server are handled by a dual system: remote procedure calls (RPCs) and netvars. Clients send actions to the server by sending RPCs, which translate to a function being run on the server (you can look at these in networkclientrpc.lua). Servers send changes in the values of netvars (normally stored in classifieds) to the clients.

 Replicas:

Spoiler
Replicas handle most of the stuff that components normally handle, but classified handle the transfer of data between the client and host. Replicas will refer to the relevant classified to get the data that would otherwise be handled by the component. For the most part, you can just change code that before referred to components to instead refer to replicas. They mainly exist to provide a nicer interface that's more similar to how components work, but really they're just a layer on top of the classifieds, which you could work with directly instead.

If you do want to make complex components like the ones that get replicated (inventory, health, etc), you can now add replicable components:



AddReplicableComponent("component name") 
So, for example, if you were adding a component for a new resource like sanity or something, let's call it "mana", you could make scripts/components/mana.lua for the component just like you would in single-player, then scripts/components/mana_replica.lua for the replica (refer to health, sanity, etc and their replicas for examples), and then call AddReplicableComponent("mana") to add it to the list of components that gets replicated for clients

Classifieds:

Spoiler
There are fewer classifieds: container, inventory, inventoryitem, and player. The basic idea of these is to be an entity that networked variables (or net_vars) are attached to. They could be attached to the base item instead, but putting them together in the classified helps bundle all the code that works similarly

Networked variables:

Spoiler
These are special variables that are synced over the network (exclusively from the server to the client, and not the other way around-- that's what RPCs are for), and that when they get changed it triggers an event on the client-- these are usually called "dirty" events, because they signal that any visuals that were relying on the value are now outdated (or "dirty") and need to be updated (or "cleaned").  Most of the game's net variables are a bit overwhelming to look at, but PeterA's The Hunt mod shows how to use them, and he also made a guide on all the network variables available.

When setting up a network variable, there are several key considerations. They attach to a specific entity via the GUID, so choosing the right entity is important. You can either ride onto existing game entities, or you can create your own like the classifieds. Then you need to make sure that whatever events happen on the server are hooked up to setting the network variables. Then, if the client needs to know when a network variable has changed (usually ones that require a visual update as a result, as opposed to ones where the client just looks at the value when it needs to), you can specify an event to be triggered when the value changes.

Remote Procedure Calls (RPCs):

Spoiler
Don't be intimidated by the fancy name; these are just the game's way of clients sending commands to the server (such as "have my character open that chest!"). Making a custom RPC is very easy (doing this in the modmain is simplest, and don't change the "modname" part to anything else, write literally "modname" -- this makes sure there's no clashing between mods, for example if there's another one that decided to call their RPC "GrowGiant"):



--This is the function we'll call remotely to do it's thing, in this case make you giant!
local function GrowGiant(player)
	player.Transform:SetScale(2,2,2)
end
--This adds the handler, which means that if the server gets told "GrowGiant",
-- it will call our function, GrowGiant, above
AddModRPCHandler(modname, "GrowGiant", GrowGiant)
--This has it send the RPC to the server when you press "v"
local function SendGrowGiantRPC()
	SendModRPCToServer(MOD_RPC[modname]["GrowGiant"])
end
--This just uses keycodes, which you can look up online. This one is "v".
GLOBAL.TheInput:AddKeyDownHandler(118, SendGrowGiantRPC)
However it may be useful to understand how they work even if you're not going to make your own. Sometimes you may need to modify certain RPCs to get a mod to work-- it ended up being necessary to get Geometry mods to work, for example. You can take a look at how they get handled server-side in the networkclientrpc.lua file. As for where they get sent to the server, it's a bit distributed throughout the code, but much of it is in the playercontroller component. Unfortunately, it's a complicated and hard-to-read component.

Simplex's explanation of the purposes of replicas and classifieds:

Spoiler
  On 12/25/2014 at 12:30 AM, simplex said:
There's a lot of overlap between replicas and classified, and there isn't something that can be done with one that can't be done with the other. The major functional difference is their main goal: replicas are mostly used to make data available on clients, while classifieds are mostly used to respond to changes on serverside data. Other than that, it's mostly a matter of efficiency. Netvars are each bound to an entity, and every netvar bound to a single entity must have a unique name (by name I mean the second parameter to their constructors). If binding many netvars to a single entity, in order to achieve uniqueness a longer name must be used, which incurs network overhead since that string must be transmitted (at least on initialisation, when pairing server and client netvars, but depending on how the engine implements it the string may be transmitted whenever the netvar's value changes). By using a separate entity to hold netvars, the classified entity, shorter names may be used without the risk of clashes.
Expand  
 

Components previously attached to players

 The main other engine change that I'm aware of is that some components that were before attached to the player are now attached to the world, instead (such as hounded, hunter, and kramped). Additionally, many of the components attached to the world have been rewritten to sync over the network and are currently pretty unmoddable (that includes clock, weather, ambientlighting, etc). As part of this, some things that were previously handled by ListenForEvent are now handled by WatchWorldState. Looking at worldstate.lua (in components) is the best way to see what was changed, but pretty much any clock/weather related events are now accessed by WatchWorldState.

Component Actions

Spoiler
For this, you need to write a function that determines whether or not the action should be added. The details of this function are application-specific, so I'll just do an overview of some of the options and then provide two examples from my Throwable Spears mod.
 
You use the function AddComponentAction(actiontype, component, fn). component is the name of the component that lets you use this action. actiontype determines what arguments are passed to fn, and in what situations it's checked at all. fn is the function that determines whether the action is added based on the arguments.

Action types (this is just compiled from looking at componentactions.lua-- for all of these you can look at how the game categorizes them by looking at where they're placed in componentactions.lua, and you should definitely do this when starting to write a component action):

SCENE - uses the arguments inst (the thing with the component), doer (the player doing the action), actions (which is where you add the action if it should be added-- all action types have this argument at the end), and right (whether the click was a right-click). SCENE actions are ones that are done by clicking on a specific thing, either in the inventory or in the world. The thing that is clicked on is what has the component that enables the action, as opposed to USEITEM and EQUIPPED, which enable actions on other things by items on your cursor or in your inventory. An example is harvesting for crops.
USEITEM - uses the arguments inst, doer, target (the thing being clicked on), actions, and right. USEITEM actions are ones where you have an item on your cursor, and are clicking it onto something in the world. For example, fueling a fire.
POINT - uses the arguments inst, doer, pos (the position that was clicked), actions, and right. POINT actions are enabled by a variety of things (having an item equipped, or having an item on the cursor), but are the only kind that are applied to a point in the world rather than a target. One example is deployable-- planting things and setting traps. Another example is teleporting with the Lazy Explorer (or "poof staff").
EQUIPPED - uses the arguments inst, doer, target, actions, right. EQUIPPED actions are enabled by having a particular item equipped. Some examples are lighting things on fire with torches, or pickaxes for mining rocks, or weapons for attacking.
INVENTORY - uses the arguments inst, doer, actions, right. INVENTORY actions are ones you do by (right-)clicking on an item in your inventory, such as eating, equipping, healing, etc.
 The main consideration in writing these functions that's different in DST from collecting actions in DS is that the component action function runs on the client and the host. So you can't just access components as if you're the host; you need to work with replicas and tags.
 
In Throwable Spears, I wanted people to be able to both target the ground near an enemy (this makes it easier to throw at moving players, for example), and to be able to click directly on the enemy itself. So I added two component actions for it, a POINT action (for nearby the target) and an EQUIPPED action:

Spoiler


local function spearthrow_point(inst, doer, pos, actions, right)
    if right then
        local target = nil
        local cur_time = GLOBAL.GetTime()
        if RANGE_CHECK then
            for k,v in pairs(GLOBAL.TheSim:FindEntities(pos.x, pos.y, pos.z, 2)) do
                if v.replica and v.replica.combat and v.replica.combat:CanBeAttacked(doer) and
                    doer.replica and doer.replica.combat and doer.replica.combat:CanTarget(v)
                    and (not v:HasTag("wall")) and (pvp or ((not pvp)
                    and (not (doer:HasTag("player") and v:HasTag("player")))))
                then
                    target = v
                    break
                end
            end
        end
        if target or not RANGE_CHECK then
            table.insert(actions, GLOBAL.ACTIONS.SPEARTHROW)
        end
    end
end

AddComponentAction("POINT", "spearthrowable", spearthrow_point)

local function spearthrow_target(inst, doer, target, actions, right)
    local pvp = GLOBAL.TheNet:GetPVPEnabled()
    local cur_time = GLOBAL.GetTime()
    if right and (not target:HasTag("wall"))
             and doer.replica.combat ~= nil
             and doer.replica.combat:CanTarget(target)
             and target.replica.combat:CanBeAttacked(doer)
             and (pvp or ((not pvp)
             and (not (doer:HasTag("player") and target:HasTag("player")))))
    then
        table.insert(actions, GLOBAL.ACTIONS.SPEARTHROW)
    end
end

AddComponentAction("EQUIPPED", "spearthrowable", spearthrow_target)
 

Other miscellaneous differences

Spoiler
Recipes-- since the recipe table needs to be the same on both the client and the host, you can no longer put recipes in character prefabs. There's now an argument at the end of the recipe constructor for setting a tag that allows a character to craft the item. For example, Willow has the tag "pyromaniac", and the recipe for her lighter is specified as follows:

Recipe("lighter",
       {
           Ingredient("rope", 1),
           Ingredient("goldnugget", 2),
           Ingredient("petals", 3),
       },
       RECIPETABS.LIGHT,
       TECH.NONE,
       nil,
       nil,
       nil,
       nil,
       "pyromaniac")
Spoiler
 
Probably a few more things that aren't occurring to me now.
List of things that are currently not (nicely) moddable

  Reveal hidden contents
Other guides for DST

Spoiler
Kzisor's Guide to Modding Practices
Dleowolf's Extended Mod Character Template -- pretty much the best place to go for characters
Dryicefox's  video guides to character art (sounds, appearance, emotes, ghosts), using DleoWolf's template
Fidoop's guide on making bigportraits for characters
tetrified's guide on getting into world gen modding (not really specific to DST, but it's not a topic covered much)
Full list of the net variables and a description of how they work.
Sample mod (The Hunt) written by Klei's PeterA to showcase how to use net variables'
An idiot's guide to making custom facial hair (how to make beards)
Make some, and I'll post them here!
Selected useful guides from the single-player mod forums

Spoiler
Wots The Diff?? -- please please read this. I linked it above, but it's so important for understanding the game's code
Malacath's guide to creating an equippable item from scratch -- a few things missing from this, but you can find them in the animation pipeline thread
TheDanaAddams' general guide to working with art assets and different approaches you can use
Mobbstar's introduction to components -- keep in mind that many components have changed for DST, but this may be useful for you before you get familiar with the game's components. Personally I just read the code now and use find-in-files, since it's faster.
I didn't do a ton of modding back then, so if you find another one and think it should be here, let me know!
 

Hopefully this guide was helpful, and if you have anything you think I should add (especially more things we specifically can't do, or need to be done slightly differently in DST), definitely let me know!

Like 44
Thanks 7
Big Ups 2
Dryicefox
Dryicefox
Registered Users
 551
 Visited by the Title Fairy 
Posted December 24, 2014
More modding guides for physical appearances and sounds can be found here:

 

Currently it is:

Character Appearance (Sample mod has been made by DleoWolf)

Character Sounds (Sample mod coming soon)

Character Ghost (Sample mod has been made by DleoWolf)

 

http://forums.kleientertainment.com/topic/43234-dont-starve-modding-guides-in-videos/#entry592483

Like 5
simplex
simplex
Registered Users
 5.3k
 Visited by the Title Fairy 
Posted December 25, 2014 (edited)
Great guide. I just have a few remarks.

The first one is a bit nitpicky, and really just a matter of terminology. You use the term "lazy evaluation" as a synonym for the aptly named minimal/short circuit evaluation, however lazy evaluation means another thing entirely. It refers to an idiom mostly found in functional programming where an expression is not evaluated immediately, but only when needed, and then caching that computed result for subsequent uses of the expression. If you recall my implementation of the IsDST function, that's an example of lazy evaluation (and so are the GetPlayer and GetWorld functions from singleplayer DS).

EDIT: Well, yeah, it's not really wrong to call short-circuit evaluation "lazy". The Wikipedia article I linked to even states "Short-circuit evaluation of Boolean control structures is sometimes called lazy". This is just not the standard notion of what lazy evaluation means. I feel quite pedantic for this remark, don't take it too seriously.

 

  On 12/22/2014 at 7:28 PM, rezecib said:
local thing = condition and if_true or if_false
This is equivalent to the following:
local thing = nilif condition then    thing = if_trueelse    thing = if_falseend
It's usually equivalent, yes, but not if the if_true expression may be false or nil itself.

 

  On 12/22/2014 at 7:28 PM, rezecib said:
(pairs) goes through the tables key/value pairs in the order that they were added.

It actually does not. It goes through all the key/value pairs in an unspecified order (pairs uses next internally). By running

  Reveal hidden contents
in the standard Lua 5.1.5 interpreter I get the output

  Reveal hidden contents
Only ipairs ensures iteration order (being restricted to the array part of a table). Otherwise, if you want orderly transversal, you'll need to first store the keys in an array-like table, sort it as you wish, and then transverse the original table using the keys from the order listed in this auxiliary table.

 

  On 12/22/2014 at 7:28 PM, rezecib said:
Another thing to note is that the new things (replicas and classifieds) have to be accessed with AddClassPostConstruct, even though they're in the components and prefabs folders (respectively).

This is true for replicas, but not classifieds. Classifieds are not classes, but prefabs, which themselves are decorations of the EntityScript class. AddClassPostConstruct won't work for them, you should (and must) use AddPrefabPostInit or equivalent.

 

  On 12/22/2014 at 7:28 PM, rezecib said:
I'll write more on this when I have a better grasp of it.

There's a lot of overlap between replicas and classified, and there isn't something that can be done with one that can't be done with the other. The major functional difference is their main goal: replicas are mostly used to make data available on clients, while classifieds are mostly used to respond to changes on serverside data. Other than that, it's mostly a matter of efficiency. Netvars are each bound to an entity, and every netvar bound to a single entity must have a unique name (by name I mean the second parameter to their constructors). If binding many netvars to a single entity, in order to achieve uniqueness a longer name must be used, which incurs network overhead since that string must be transmitted (at least on initialisation, when pairing server and client netvars, but depending on how the engine implements it the string may be transmitted whenever the netvar's value changes). By using a separate entity to hold netvars, the classified entity, shorter names may be used without the risk of clashes.

 

  On 12/22/2014 at 7:28 PM, rezecib said:
Custom RPCs (remote procedure calls). It's possible to hack around this with net variables

Netvars in and of themselves can't replace RPCs because they're the dual form of communication. DST's RPCs are client -> server RPCs. Netvars, on the other hand, when set on a client don't get updated on the server, only the other way around (so they only allow server -> client communication).

The way I implemented custom RPCs in Up and Away was by realising an RPC's code is only truly relevant on the server, i.e. it is only on the server that the code must match the desired function, clients only need to know the correct code to use. So what I did was, on the server, add a single custom RPC to the next code available. Then, on the server, I set a (custom) netvar, attached to the world_network entity, to the dynamically obtained code. This netvar's value is then used by clients to determine the correct code to use. This single custom RPC I directly add is in fact a nested RPC dispatcher, which receives as its first parameter a numerical subcode value. This subcode value is the index to be used in U&A's custom RPC table to obtain the actual RPC handler to run.

It works and it's pretty robust, however it's far from a simple system.

 

  On 12/22/2014 at 7:28 PM, rezecib said:
Custom containers (there's a workaround possible for creating containers with the same layout as an existing game container, but making anything with custom slot sizes is pretty awful).

It's awful, yes, but not impossible. U&A's custom container (kettle, refiner and cauldron), all of which have different layouts from vanilla ones, have been fully ported. Their implementation isn't as robust as I'd like, though; hopefully we'll get a more modder friendly setup soon.

Edited December 25, 2014 by simplex
Like 12
Thanks 1
Maris
Maris
Registered Users
 950
  
Posted December 25, 2014
  On 12/22/2014 at 7:28 PM, 'rezecib said:
for i,v in ipairs(DST_CHARACTERLIST) do-- do stuff to the i (index) and v (value) pair that it got from the table-- the first loop has i == 1, v == "wilson"-- the first loop has i == 2, v == "willow"-- the first loop has i == 3, v == "wx78"-- the first loop has i == 4, v == "wickerbottom"end
​

for i=1,#DST_CHARACTERLIST do   local v=DST_CHARACTERLIST[i]   --- the same i and vend
​

rezecib
rezecib
Registered Users
 3.9k
 Visited by the Title Fairy 
Author
Posted December 25, 2014 (edited)
@simplex, Thanks for the very detailed input! I've been going through it and editing it into the post. I'm guessing it was pretty clear to you that most of my CS experience is pretty informal, so it's awesome to have input from someone with much better grounding in the field!

 

 

 

  On 12/25/2014 at 12:30 AM, simplex said:
You use the term "lazy evaluation"
I wrote the rough draft calling it lazy evaluation, then decided to check that and got reminded it was called minimal/short-circuit evaluation. Looks like I missed the last case where I called it lazy evaluation, though xD. Fixed now!

 

 

 

  On 12/25/2014 at 12:30 AM, simplex said:
It's usually equivalent, yes, but not if the if_true expression may be false or nil itself.
Oh, good point. I changed it to have "if condition and if_true then", and noted that if if_true is not nil or false, then it will work like the intuitive block I had before.

 

 

 

  On 12/25/2014 at 12:30 AM, simplex said:
It actually does not. It goes through all the key/value pairs in an unspecified order (pairs uses next internally).
 I read that when I was looking it up, but when I tested it, it was always going through in the order added. I'll add a note on that, though. I also added a note on ipairs only going until a value is nil.

 

 

 

  On 12/25/2014 at 12:30 AM, simplex said:
This is true for replicas, but not classifieds.
Oops. Fixed :grin:

 

 

 

  On 12/25/2014 at 12:30 AM, simplex said:
There's a lot of overlap between replicas and classified
 I think I'll quote you on this in the main post for now, you've said it much better than I can. Hopefully I'll get some examples in there later, though.

 

 

 

  On 12/25/2014 at 12:30 AM, simplex said:
Netvars in and of themselves can't replace RPCs because they're the dual form of communication. DST's RPCs are client -> server RPCs. Netvars, on the other hand, when set on a client don't get updated on the server, only the other way around (so they only allow server -> client communication).
Everything is illuminated! I incorporated this into the engine differences summary :grin:

 

 

 

  On 12/25/2014 at 12:30 AM, simplex said:
The way I implemented custom RPCs in Up and Away
I added this under the note that custom RPCs can't be nicely implemented yet. Maybe your implementation will help get us a more integrated system for custom RPCs from Peter sooner :grin:

 

 

 

  On 12/25/2014 at 12:30 AM, simplex said:
It's awful, yes, but not impossible.
Thanks, I noted the possibility. Although I think that anyone who could figure out how to do it probably doesn't need a guide :razz:

 

@Maris, It's nice to avoid typing DST_CHARACTERLIST twice if you don't have to :razz:

 

Edit: Argh, it ate my edits the first time because I submitted this response just before it. I think I got all of them back in now, though.

 

Edited December 25, 2014 by rezecib