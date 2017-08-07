import Tkinter as tk
import rospy
from std_msgs.msg import String
from datetime import datetime
import pickle
import time
import thread


class Application(tk.Frame):
    def __init__(self, master=None):
        rospy.init_node('ros_recorder')
        tk.Frame.__init__(self, master)
        self.grid()
        self.create_widgets()
        self.rec = False
        self.record_list = []
        self.filename = ''

    def start_listening(self):

        for topic in self.record_list:
            rospy.Subscriber(topic, String, self.callback)

    def create_widgets(self):

        self.frame_record = tk.LabelFrame(self, labelanchor='nw', text='RECORD ANIMATION BLOCK')
        self.frame_record.grid(column=0, row=0)

        self.label_saveas = tk.Label(self.frame_record, text='save as')
        self.label_saveas.grid(column=0, row=0)

        self.text_save_file = tk.Entry(self.frame_record, width=50)
        self.text_save_file.insert(tk.END, 'bag_1')
        self.text_save_file.grid(column=1, row=0)

        self.label_topics = tk.Label(self.frame_record, text='Topics')
        self.label_topics.grid(column=0, row=1)

        self.text_record_list = tk.Entry(self.frame_record, width=50)
        self.text_record_list.insert(tk.END, 'skeleton_angles')
        self.text_record_list.grid(column=1, row=1)

        self.label_playback_file = tk.Label(self.frame_record, text='playback file')
        self.label_playback_file.grid(column=0, row=2)

        self.text_load_file = tk.Entry(self.frame_record, width=50)
        self.text_load_file.insert(tk.END, ' ')
        self.text_load_file.grid(column=1, row=2)

        self.button_record = tk.Button(self.frame_record, text='record', command=self.start_record)
        self.button_record.grid(column=0, row=3)

        self.button_stop_rec = tk.Button(self.frame_record, text='stop', command=self.stop)
        self.button_stop_rec.grid(column=0, row=4)

        # self.frame_playback = tk.LabelFrame(self, labelanchor='nw', text='PLAYBACK')
        # self.frame_playback.grid(column=1, row=0)

        # self.button_play = tk.Button(self.frame_playback, text='play', command=self.play)
        # self.button_play.grid(column=0, row=1)

    def start_record(self):
        self.record()
        self.play()

    def record(self):
        thread.start_new_thread(self.record_thread, (None, None))

    def record_thread(self, arg1=None, arg2=None):
        self.rec_bag = []
        self.rec = True
        self.record_list = self.text_record_list.get().split(',')
        print('record topics: ', self.record_list)
        self.start_listening()

    def stop(self):
        self.filename = self.text_save_file.get()
        self.rec = False

        # save to file

        # shift all times to dt
        t0 = self.rec_bag[0][0]
        for item in self.rec_bag:
            item = (item[0] - t0, item[1], item[2])

        # sort according to time (for multiple topics)

        with open(self.filename, 'wb') as output:
            pickle.dump(self.rec_bag, output, pickle.HIGHEST_PROTOCOL)
        print('done saving!')

    def callback(self, data):
        if self.rec:
            self.rec_bag.append((datetime.now(), data._connection_header['topic'], data.data))

    def play(self):
        thread.start_new_thread(self.play_thread, (None, None))

    def play_thread(self, arg1=None, arg2=None):
        self.filename = self.text_load_file.get()
        with open(self.filename, 'rb') as input:
            self.play_bag = pickle.load(input)

        # get all topics
        topic_list = set()
        for item in self.play_bag:
            topic_list.add(item[1])
        print(topic_list)

        publishers = {}
        for topic in topic_list:
            publishers[topic] = rospy.Publisher (topic, String, queue_size=10)

        old_item = self.play_bag[0]
        publishers[old_item[1]].publish(old_item[2])
        for iter in range(1, len(self.play_bag)):
            new_item = self.play_bag[iter]
            dt = (new_item[0] - old_item[0]).total_seconds()
            print(dt, new_item)
            time.sleep(dt)
            publishers[new_item[1]].publish(new_item[2])
            old_item = new_item
        print('done playing!')

app = Application()
app.master.title('Sample application')
app.mainloop()