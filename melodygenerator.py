#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 17:44:14 2020

@author: balamuruga
"""

import tensorflow.keras as keras
import json
import numpy as np
import music21 as m21
from preprocess2 import SEQUENCE_LENGTH,MAPPING_PATH
class MelodyGenerator:
    
    def __init__(self,model_path ="model.h5"):
        
        self.model_path = model_path
        self.model = keras.models.load_model(model_path)
        
        with open(MAPPING_PATH,"r") as fp:
            self._mapping = json.load(fp)
            
        self._start_symbols = ["/"] * SEQUENCE_LENGTH
        

    def generate_melody(self,seed,num_steps, max_sequence_length, temperature):
        
        #create seed with start symbols
        seed = seed.split()
        melody = seed
        
        seed = self._start_symbols+seed
        
        #map seed to integers
        seed = [self._mapping[symbol] for symbol in seed]
        
        for _ in range(num_steps):
            
            # limit the seed to max_sequence_length
            
            seed = seed[-max_sequence_length:]
            
            # one-hot encode the seed
            
            onehot_seed = keras.utils.to_categorical(seed, num_classes = len(self._mapping))
            
            #(1, max_sequence_length, num of symbols in the vocabulory,)
                
            onehot_seed = onehot_seed[np.newaxis, ...]
            
            #make a prediction
            probabilities = self.model.predict(onehot_seed)[0]
            
            # [0.1,0.2,0.1,0.6] -> 1
            output_int = self._sample_with_temperature(probabilities,temperature)
            
            #update the seed
            seed.append(output_int)
            
            #map int to our encoding
            output_symbol = [k for k,v in self._mapping.items() if v==output_int][0]
            
            # check whether we're at the end of a melody
            if output_symbol=="/":
                break
            melody.append(output_symbol)
            
        return melody
            
            
    def _sample_with_temperature(self,probabilities,temperature):
        # if temperature --> infinity 
        #if temperature --> 0
        #temperature =1
        
        predictions =np.log(probabilities)/temperature
        probabilities = np.exp(predictions)/np.sum(np.exp(predictions))
        
        choices = range(len(probabilities))
        index = np.random.choice(choices,p=probabilities)
        
        return index
    def save_melody(self,melody, step_duration=0.25,format="mid",file_name="mel.midi"):

        #create a music21 stream
        stream = m21.stream.Stream()
        #parse all the symbols in the melody and create note,rest objects
        #60_ _ _ r _ _ 62 _ 
        start_symbol = None
        step_counter = 1 
        
        for i,symbol in enumerate(melody):
            # handle case in which we have a note/rest:
            if symbol != "_" or i+1 ==len(melody):
                #ensure we are dealing with note/rest beyond the first one
                if start_symbol is not None:
                    quarter_length_duration  =step_duration*step_counter
                    
                    #handle rest
                    if start_symbol=="r":
                        m21_event = m21.note.Rest(quarter_length=quarter_length_duration)
                        
                    # handle note
                    else:
                        m21_event = m21.note.Note(int(start_symbol), quarterLength=quarter_length_duration)

                    stream.append(m21_event)

                    # reset the step counter
                    step_counter = 1

                start_symbol = symbol

            # handle case in which we have a prolongation sign "_"
            else:
                step_counter += 1
        
        #write the m21 stream to a midi files
        
        stream.write(format,file_name)
if __name__ == "__main__":
    mg = MelodyGenerator()
    seed ="67 _ 65 _ _ _ 60 _ _ _ _ _ 62 _ 64"
    melody = mg.generate_melody(seed, 500, SEQUENCE_LENGTH,0.8)
    print("Melody: ",melody)
    mg.save_melody(melody)
    
    