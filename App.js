import React, { useState, useEffect } from "react";
import { View, Text, Button, TextInput } from "react-native";
import WebSocket from "isomorphic-ws";

export default function App() {
    const [message, setMessage] = useState("");
    const [receivedMessages, setReceivedMessages] = useState([]);
    const [serverIP, setServerIP] = useState("ws://192.168.1.100:8080"); // Change to your actual IP

    let ws;

    useEffect(() => {
        ws = new WebSocket(serverIP);

        ws.onopen = () => {
            console.log("Connected to server");
        };

        ws.onmessage = (event) => {
            console.log("Received:", event.data);
            setReceivedMessages(prev => [...prev, event.data]); // Append new message to state
        };

        ws.onerror = (error) => {
            console.log("WebSocket Error:", error);
        };

        ws.onclose = () => {
            console.log("Disconnected from server");
        };

        return () => {
            ws.close();
        };
    }, [serverIP]);

    const sendMessage = () => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(message);
            setMessage(""); // Clear input field
        } else {
            console.log("WebSocket is not connected");
        }
    };

    return (
        <View style={{ flex: 1, justifyContent: "center", alignItems: "center", padding: 20 }}>
            <Text>Enter Server IP:</Text>
            <TextInput
                value={serverIP}
                onChangeText={setServerIP}
                style={{ height: 40, borderColor: "gray", borderWidth: 1, marginBottom: 10, width: "80%", padding: 5 }}
                placeholder="ws://192
